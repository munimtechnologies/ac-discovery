/* Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0). */
/*
 * acc02.c: job acc02's search for the SAIR / Caltech Andrews-Curtis Conjecture Challenge
 * (Discovery Track), predictions in acc02-predictions.md, written before the job ran.
 *
 * acc01 searched the 14 explicit AC moves and spent most of its nodes on conjugates of one
 * state. acc02 searches pairs of cyclically reduced relators taken up to cyclic permutation and
 * inversion (and up to swapping the two), with one kind of step:
 *
 *     r_i -> the cyclic reduction of rot_a(r_i^s) rot_b(r_j)^e      (s, e = +-1)
 *
 * that is, r_i times any conjugate of r_j^(+-1). A step is realized by explicit moves of the
 * verifier's move set (ac-r2-v1, as in acc01.py): an inversion if s = -1, conjugations by single
 * letters that rotate r_i to rotation a and r_j to rotation b (min(a, n - a) moves each), one
 * multiplication (moves 2 to 5), and conjugations that cyclically reduce the product. The search
 * is greedy best-first by total length (then by explicit moves so far), stops at total length 2
 * (two single letters) and prints the explicit path from the presentation as given; acc02.py
 * finishes it to exactly (x, y) with acc01's ball and checks it with the challenge's verifier.
 *
 * Every step of a found path is replayed with the explicit moves and compared with the stored
 * state (status ERROR if they differ). Visited classes are kept as 64-bit hashes of a canonical
 * form, so a hash collision could only hide a state, never produce a wrong path.
 *
 * Input lines: "<id> <r0> <r1>", words over x X y Y (X = x^-1, Y = y^-1; "-" is the empty word).
 * Output lines: "<id> <SOLVED|NONE|SKIP|ERROR|LONG> <pops> <stored> <moves> <seconds> <path>",
 * the path comma-separated ("-" if none).
 *
 * Usage: acc02 [--grow G] [--slack K] [--max-total T] [--pops N] [--seconds S] [--nodes N]
 *        acc02 --selftest
 */
#define _POSIX_C_SOURCE 199309L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAXL 64                 /* longest relator a search state may hold */
#define BUF (4 * MAXL)
#define MAXPATH 100000          /* the verifier's move limit */

typedef signed char let;

typedef struct {
    int32_t parent, cost;
    uint8_t n[2], i, s, e, a, b;
    let w[2][MAXL];
} Node;

typedef struct { int32_t pri, cost, idx; } Item;

typedef struct { int n[2]; let w[2][BUF]; } State;

typedef struct { int grow, slack, max_total; int64_t max_pops; double seconds; } Params;

static const let GEN[4] = {1, -1, 2, -2};

static Node *nodes;
static int64_t n_nodes, cap_nodes;
static uint64_t *table;
static uint64_t mask;
static Item *heap;
static int64_t heap_n;
static int path[MAXPATH];
static int path_n, path_over;

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ---------- words and the explicit moves ---------- */

static void inv_word(const let *w, int n, let *out) {      /* out must not alias w */
    for (int k = 0; k < n; k++) out[k] = -w[n - 1 - k];
}

/* a := the free reduction of a b, for reduced a and b (cancellation only at the junction) */
static int join_into(let *a, int na, const let *b, int nb) {
    int k = 0;
    while (k < na && k < nb && a[na - 1 - k] == -b[k]) k++;
    int m = na - k;
    for (int t = k; t < nb; t++) a[m++] = b[t];
    return m;
}

static int conj_move(int i, let g) {                       /* r_i -> g r_i g^-1 */
    int k = g == 1 ? 0 : g == -1 ? 1 : g == 2 ? 2 : 3;
    return (i == 0 ? 6 : 10) + k;
}

static void apply_move(State *S, int m) {
    let tmp[BUF];
    if (m == 0 || m == 1) {
        int n = S->n[m];
        inv_word(S->w[m], n, tmp);
        memcpy(S->w[m], tmp, n);
    } else if (m <= 5) {
        int i = m <= 3 ? 0 : 1, j = 1 - i;
        if (m == 2 || m == 4)
            memcpy(tmp, S->w[j], S->n[j]);
        else
            inv_word(S->w[j], S->n[j], tmp);
        S->n[i] = join_into(S->w[i], S->n[i], tmp, S->n[j]);
    } else {
        int i = m < 10 ? 0 : 1, k = 0;
        let g = GEN[(m - 6) % 4], h = -g;
        tmp[k++] = g;
        k = join_into(tmp, k, S->w[i], S->n[i]);
        k = join_into(tmp, k, &h, 1);
        memcpy(S->w[i], tmp, k);
        S->n[i] = k;
    }
}

static void emit(State *S, int m) {
    apply_move(S, m);
    if (path_n < MAXPATH)
        path[path_n++] = m;
    else
        path_over = 1;
}

/* rotate the cyclically reduced r_i to rot_a: left by one is conjugation by w_0^-1, right by
   one conjugation by w_(n-1) */
static void rotate(State *S, int i, int a) {
    int n = S->n[i];
    if (n < 2 || a % n == 0) return;
    a %= n;
    if (a <= n - a)
        for (int t = 0; t < a; t++) emit(S, conj_move(i, -S->w[i][0]));
    else
        for (int t = 0; t < n - a; t++) emit(S, conj_move(i, S->w[i][S->n[i] - 1]));
}

/* cyclically reduce r_i: g s g^-1 -> s by conjugation with g^-1 */
static void strip(State *S, int i) {
    while (S->n[i] >= 2 && S->w[i][0] == -S->w[i][S->n[i] - 1])
        emit(S, conj_move(i, -S->w[i][0]));
}

static int rot_cost(int a, int n) { return a < n - a ? a : n - a; }

/* ---------- canonical forms and the visited set ---------- */

static int rank(let l) { return l > 0 ? 2 * (l - 1) : 2 * (-l - 1) + 1; }

/* the least rotation of w or of w^-1, as letter ranks */
static void canon(const let *w, int n, uint8_t *out) {
    uint8_t f[MAXL], r[MAXL];
    for (int k = 0; k < n; k++) {
        f[k] = (uint8_t)rank(w[k]);
        r[k] = (uint8_t)rank(-w[n - 1 - k]);
    }
    const uint8_t *best = f;
    int bo = 0;
    for (int src = 0; src < 2; src++) {
        const uint8_t *v = src ? r : f;
        for (int o = 0; o < n; o++) {
            if (src == 0 && o == 0) continue;
            int d = 0;
            for (int t = 0; t < n && !d; t++) d = (int)v[(o + t) % n] - (int)best[(bo + t) % n];
            if (d < 0) { best = v; bo = o; }
        }
    }
    for (int t = 0; t < n; t++) out[t] = best[(bo + t) % n];
}

static uint64_t mix(uint64_t z) {
    z += 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

static uint64_t hash_word(const let *w, int n) {
    uint8_t c[MAXL];
    canon(w, n, c);
    uint64_t h = 1469598103934665603ULL ^ (uint64_t)n;
    for (int t = 0; t < n; t++) {
        h ^= (uint64_t)c[t] + 1;
        h *= 1099511628211ULL;
    }
    return mix(h);
}

static uint64_t pair_key(uint64_t ha, uint64_t hb) {      /* unordered: the pair up to swap */
    uint64_t lo = ha < hb ? ha : hb, hi = ha < hb ? hb : ha;
    uint64_t k = mix(lo * 0x100000001b3ULL + hi) ^ hi;
    return k ? k : 1;
}

static int insert_key(uint64_t h) {
    uint64_t k = h & mask;
    while (table[k]) {
        if (table[k] == h) return 0;
        k = (k + 1) & mask;
    }
    table[k] = h;
    return 1;
}

/* ---------- the priority queue ---------- */

static int less(const Item *x, const Item *y) {
    if (x->pri != y->pri) return x->pri < y->pri;
    if (x->cost != y->cost) return x->cost < y->cost;
    return x->idx < y->idx;
}

static void push(Item it) {
    int64_t k = heap_n++;
    while (k > 0) {
        int64_t p = (k - 1) / 2;
        if (!less(&it, &heap[p])) break;
        heap[k] = heap[p];
        k = p;
    }
    heap[k] = it;
}

static Item pop(void) {
    Item top = heap[0], last = heap[--heap_n];
    int64_t k = 0;
    for (;;) {
        int64_t c = 2 * k + 1;
        if (c >= heap_n) break;
        if (c + 1 < heap_n && less(&heap[c + 1], &heap[c])) c++;
        if (!less(&heap[c], &last)) break;
        heap[k] = heap[c];
        k = c;
    }
    if (heap_n > 0) heap[k] = last;
    return top;
}

/* ---------- the search ---------- */

static void realize(State *S, const Node *c) {
    int i = c->i, j = 1 - i;
    if (c->s) emit(S, i);                                  /* move 0 or 1 */
    rotate(S, i, c->a);
    rotate(S, j, c->b);
    emit(S, i == 0 ? (c->e ? 3 : 2) : (c->e ? 5 : 4));
    strip(S, i);
}

static int same(const State *S, const Node *c) {
    return S->n[0] == c->n[0] && S->n[1] == c->n[1] && !memcmp(S->w[0], c->w[0], c->n[0])
           && !memcmp(S->w[1], c->w[1], c->n[1]);
}

enum { SOLVED = 1, NONE = 0, SKIP = -1, ERROR = -2, LONG = -3 };

/* search from S (the presentation as given); on SOLVED, path[0..path_n) leads to total length 2 */
static int search(State S, const Params *P, int64_t *pops_out, double t0) {
    path_n = path_over = 0;
    n_nodes = heap_n = 0;
    *pops_out = 0;
    for (int i = 0; i < 2; i++) {
        if (S.n[i] > MAXL) return SKIP;
        strip(&S, i);
        if (S.n[i] == 0) return ERROR;
    }
    if (S.n[0] + S.n[1] == 2) return SOLVED;
    int max_total = S.n[0] + S.n[1] + P->slack;
    if (P->max_total < max_total) max_total = P->max_total;
    memset(table, 0, (mask + 1) * sizeof(uint64_t));
    Node *root = &nodes[n_nodes++];
    memset(root, 0, sizeof(Node));
    root->parent = -1;
    for (int i = 0; i < 2; i++) {
        root->n[i] = (uint8_t)S.n[i];
        memcpy(root->w[i], S.w[i], S.n[i]);
    }
    insert_key(pair_key(hash_word(root->w[0], root->n[0]), hash_word(root->w[1], root->n[1])));
    push((Item){S.n[0] + S.n[1], 0, 0});
    int64_t pops = 0, goal = -1;
    int full = 0;
    let U[MAXL], Vb[MAXL], W[MAXL], buf[2 * MAXL];
    while (heap_n > 0 && goal < 0 && !full) {
        if (pops >= P->max_pops) break;
        if ((pops & 255) == 0 && now() - t0 > P->seconds) break;
        Item it = pop();
        pops++;
        const Node *p = &nodes[it.idx];
        int ptot = p->n[0] + p->n[1];
        for (int i = 0; i < 2 && goal < 0 && !full; i++) {
            int j = 1 - i, nU = p->n[i], nV = p->n[j];
            uint64_t hV = hash_word(p->w[j], nV);
            for (int s = 0; s < 2 && goal < 0 && !full; s++) {
                if (s)
                    inv_word(p->w[i], nU, U);
                else
                    memcpy(U, p->w[i], nU);
                for (int a = 0; a < nU && goal < 0 && !full; a++) {
                    for (int b = 0; b < nV && goal < 0 && !full; b++) {
                        for (int t = 0; t < nV; t++) Vb[t] = p->w[j][(b + t) % nV];
                        inv_word(Vb, nV, W);
                        for (int e = 0; e < 2; e++) {
                            for (int t = 0; t < nU; t++) buf[t] = U[(a + t) % nU];
                            int m = join_into(buf, nU, e ? W : Vb, nV);
                            int lo = 0, hi = m;
                            while (hi - lo >= 2 && buf[lo] == -buf[hi - 1]) { lo++; hi--; }
                            int q = hi - lo, tot = q + nV;
                            if (q == 0 || q > MAXL || tot > ptot + P->grow || tot > max_total)
                                continue;
                            if (!insert_key(pair_key(hash_word(buf + lo, q), hV))) continue;
                            if (n_nodes >= cap_nodes) { full = 1; break; }
                            int64_t idx = n_nodes++;
                            Node *ch = &nodes[idx];
                            ch->parent = it.idx;
                            ch->n[i] = (uint8_t)q;
                            ch->n[j] = (uint8_t)nV;
                            memcpy(ch->w[i], buf + lo, q);
                            memcpy(ch->w[j], Vb, nV);
                            ch->i = (uint8_t)i;
                            ch->s = (uint8_t)s;
                            ch->e = (uint8_t)e;
                            ch->a = (uint8_t)a;
                            ch->b = (uint8_t)b;
                            ch->cost = p->cost + s + rot_cost(a, nU) + rot_cost(b, nV) + 1 + lo;
                            if (tot == 2) { goal = idx; break; }
                            push((Item){tot, ch->cost, (int32_t)idx});
                        }
                    }
                }
            }
        }
    }
    *pops_out = pops;
    if (goal < 0) return NONE;
    int64_t len = 0;
    for (int64_t k = goal; k != 0; k = nodes[k].parent) len++;
    int32_t *chain = malloc(sizeof(int32_t) * (size_t)len);
    int64_t t = len;
    for (int64_t k = goal; k != 0; k = nodes[k].parent) chain[--t] = (int32_t)k;
    int status = SOLVED;
    for (t = 0; t < len && status == SOLVED; t++) {
        realize(&S, &nodes[chain[t]]);
        if (!same(&S, &nodes[chain[t]])) status = ERROR;
    }
    free(chain);
    if (status == SOLVED && path_over) status = LONG;
    return status;
}

/* ---------- input, output and the self-test ---------- */

static int parse_word(const char *s, let *w) {             /* -1 if too long or a bad letter */
    int n = 0;
    if (!strcmp(s, "-")) return 0;
    for (; *s; s++) {
        let l = *s == 'x' ? 1 : *s == 'X' ? -1 : *s == 'y' ? 2 : *s == 'Y' ? -2 : 0;
        if (!l || n >= BUF - 2) return -1;
        if (n && w[n - 1] == -l)
            n--;
        else
            w[n++] = l;
    }
    return n;
}

static const char *NAMES[] = {"NONE", "SOLVED"};

static const char *status_name(int r) {
    if (r >= 0) return NAMES[r];
    return r == SKIP ? "SKIP" : r == ERROR ? "ERROR" : "LONG";
}

static int state_is(const State *S, const char *a, const char *b) {
    let wa[BUF], wb[BUF];
    int na = parse_word(a, wa), nb = parse_word(b, wb);
    return S->n[0] == na && S->n[1] == nb && !memcmp(S->w[0], wa, na)
           && !memcmp(S->w[1], wb, nb);
}

static void set_state(State *S, const char *a, const char *b) {
    S->n[0] = parse_word(a, S->w[0]);
    S->n[1] = parse_word(b, S->w[1]);
}

static int selftest(const Params *P) {
    /* the explicit moves on states worked out by hand (acc01.apply) */
    static const struct { const char *a, *b; int m; const char *ra, *rb; } T[] = {
        {"xy", "y", 3, "x", "y"},     {"xy", "y", 2, "xyy", "y"},   {"x", "y", 6, "x", "y"},
        {"xy", "y", 8, "yx", "y"},    {"xy", "y", 0, "YX", "y"},    {"x", "y", 13, "x", "y"},
        {"x", "yx", 5, "x", "y"},     {"x", "yx", 4, "x", "yxx"},   {"xy", "Yx", 1, "xy", "Xy"},
        {"xyX", "y", 7, "y", "y"},    {"x", "xyX", 11, "x", "y"},   {"xY", "y", 9, "Yx", "y"},
    };
    int fails = 0;
    for (size_t k = 0; k < sizeof T / sizeof T[0]; k++) {
        State S;
        set_state(&S, T[k].a, T[k].b);
        apply_move(&S, T[k].m);
        if (!state_is(&S, T[k].ra, T[k].rb)) {
            printf("SELFTEST move %d on (%s, %s) wrong\n", T[k].m, T[k].a, T[k].b);
            fails++;
        }
    }
    /* canonical forms: the same for every rotation and for the inverse */
    uint32_t seed = 12345;
    for (int k = 0; k < 2000; k++) {
        let w[MAXL], r[MAXL], v[MAXL];
        seed = seed * 1103515245u + 12345u;
        int n = 1 + (int)((seed >> 16) % 30);
        do {
            for (int t = 0; t < n; t++) {
                do {
                    seed = seed * 1103515245u + 12345u;
                    w[t] = GEN[(seed >> 16) % 4];
                } while (t && w[t] == -w[t - 1]);
            }
        } while (n > 1 && w[n - 1] == -w[0]);
        seed = seed * 1103515245u + 12345u;
        int o = (int)((seed >> 16) % n);
        for (int t = 0; t < n; t++) r[t] = w[(o + t) % n];
        inv_word(w, n, v);
        if (hash_word(w, n) != hash_word(r, n) || hash_word(w, n) != hash_word(v, n)) {
            printf("SELFTEST canonical form not invariant (length %d)\n", n);
            fails++;
            break;
        }
    }
    /* small searches on presentations built from (x, y) by explicit moves (the last two: moves
       4, 2, 10, 3, then 5); each path replayed from the start must end at total length 2 */
    static const char *Q[][2] = {{"xy", "y"}, {"xyx", "yx"}, {"yx", "yxy"}, {"xyxYX", "xy"},
                                 {"xyxYX", "xyxyXYX"}};
    for (size_t k = 0; k < sizeof Q / sizeof Q[0]; k++) {
        State S, R;
        set_state(&S, Q[k][0], Q[k][1]);
        R = S;
        int64_t pops;
        int st = search(S, P, &pops, now());
        if (st != SOLVED) {
            printf("SELFTEST search (%s, %s): %s\n", Q[k][0], Q[k][1], status_name(st));
            fails++;
            continue;
        }
        for (int t = 0; t < path_n; t++) apply_move(&R, path[t]);
        if (R.n[0] != 1 || R.n[1] != 1) {
            printf("SELFTEST search (%s, %s): replay does not end at two letters\n", Q[k][0],
                   Q[k][1]);
            fails++;
        }
    }
    printf("SELFTEST %s %d\n", fails ? "FAIL" : "ok", fails);
    return fails ? 1 : 0;
}

int main(int argc, char **argv) {
    Params P = {4, 24, 2 * MAXL, 100000000, 2.0};
    int self = 0;
    cap_nodes = 1000000;
    for (int k = 1; k < argc; k++) {
        if (!strcmp(argv[k], "--selftest")) self = 1;
        else if (k + 1 < argc && !strcmp(argv[k], "--grow")) P.grow = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--slack")) P.slack = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--max-total")) P.max_total = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--pops")) P.max_pops = atoll(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--seconds")) P.seconds = atof(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--nodes")) cap_nodes = atoll(argv[++k]);
        else {
            fprintf(stderr, "unknown argument %s\n", argv[k]);
            return 2;
        }
    }
    uint64_t size = 1;
    while (size < 2 * (uint64_t)cap_nodes) size <<= 1;
    mask = size - 1;
    nodes = malloc(sizeof(Node) * (size_t)cap_nodes);
    table = malloc(sizeof(uint64_t) * (size_t)size);
    heap = malloc(sizeof(Item) * (size_t)cap_nodes);
    if (!nodes || !table || !heap) {
        fprintf(stderr, "out of memory\n");
        return 3;
    }
    if (self) return selftest(&P);
    static char line[8192], id[128], a[4096], b[4096];
    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, "%127s %4095s %4095s", id, a, b) != 3) continue;
        State S;
        int na = parse_word(a, S.w[0]), nb = parse_word(b, S.w[1]);
        double t0 = now();
        int64_t pops = 0;
        int st;
        if (na < 0 || nb < 0) {
            st = SKIP;
            path_n = 0;
            n_nodes = 0;
        } else {
            S.n[0] = na;
            S.n[1] = nb;
            st = search(S, &P, &pops, t0);
        }
        printf("%s %s %lld %lld %d %.3f ", id, status_name(st), (long long)pops,
               (long long)n_nodes, st == SOLVED ? path_n : 0, now() - t0);
        if (st == SOLVED && path_n > 0) {
            for (int t = 0; t < path_n; t++) printf(t ? ",%d" : "%d", path[t]);
            printf("\n");
        } else {
            printf("-\n");
        }
        fflush(stdout);
    }
    return 0;
}
