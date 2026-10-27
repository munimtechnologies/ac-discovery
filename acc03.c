/* Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0). */
/*
 * acc03.c: job acc03's path shortener for the SAIR / Caltech Andrews-Curtis Conjecture Challenge
 * (Discovery Track), predictions in acc03-predictions.md, written before the job ran.
 *
 * Only the shortest verified path on a presentation scores, and acc02's paths (median length about
 * 285) repeat the same detours. For a path with states s_0, ..., s_n, one round:
 *
 *     1. every state within R2 moves of some s_j goes into a table keyed by a 64-bit hash, with
 *        the j and the distance d2 for which j - d2 is largest;
 *     2. from i = 0: every state t within R1 moves (d1) of s_i is looked up; if the best entry has
 *        j - d1 - d2 > i, the d1 moves s_i -> t and the d2 moves t -> s_j (found again by a search
 *        from s_j, and inverted) replace the j - i moves of the path, and i jumps to j; otherwise
 *        the path's own move is kept and i moves on by one.
 *
 * A replacement is replayed and compared with s_j before it is used, so a hash collision can only
 * lose a shortcut, never make a wrong path. Rounds repeat until one gains nothing (at most
 * --rounds). The final path is replayed from the presentation and must end at the same state as
 * the input path (status ERROR otherwise, and the input path is printed unchanged).
 *
 * Moves are the verifier's (ac-r2-v1, as acc01.py): 0, 1 invert r0, r1; 2 to 5 are r0 -> r0 r1,
 * r0 r1^-1 and r1 -> r1 r0, r1 r0^-1; 6 to 9 conjugate r0 and 10 to 13 conjugate r1 by x, x^-1, y,
 * y^-1 (r -> g r g^-1). Move m is undone by INV[m].
 *
 * Input lines: "<id> <r0> <r1> <path>", words over x X y Y (X = x^-1, Y = y^-1; "-" is the empty
 * word), the path comma-separated ("-" if empty).
 * Output lines: "<id> <OK|LONG|ERROR> <old length> <new length> <rounds> <seconds> <path>".
 *
 * Usage: acc03 [--r1 R] [--r2 R] [--rounds K] [--max-entries N]
 *        acc03 --selftest
 */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <time.h>

#define MAXW 512                /* longest relator a state may hold */
#define MAXN 20000              /* longest path shortened (longer ones are printed unchanged) */
#define MAXR 4                  /* largest search radius */

typedef signed char let;

typedef struct { int n[2]; let w[2][MAXW]; } State;

static const int INV[14] = {0, 1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12};
static const let GEN[4] = {1, -1, 2, -2};

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ---------- words, states and the moves ---------- */

/* a := the free reduction of a b, for reduced a and b (cancellation only at the junction);
 * -1 if the result would be longer than MAXW (a is then unchanged) */
static int join_into(let *a, int na, const let *b, int nb) {
    int k = 0;
    while (k < na && k < nb && a[na - 1 - k] == -b[k]) k++;
    if (na + nb - 2 * k > MAXW) return -1;
    int m = na - k;
    for (int t = k; t < nb; t++) a[m++] = b[t];
    return m;
}

static void copy_state(State *d, const State *s) {
    for (int i = 0; i < 2; i++) {
        d->n[i] = s->n[i];
        memcpy(d->w[i], s->w[i], s->n[i]);
    }
}

static int same(const State *a, const State *b) {
    return a->n[0] == b->n[0] && a->n[1] == b->n[1] && !memcmp(a->w[0], b->w[0], a->n[0])
           && !memcmp(a->w[1], b->w[1], a->n[1]);
}

/* T := move m applied to S (T must not alias S); 0 if a relator would pass MAXW */
static int apply_to(const State *S, int m, State *T) {
    let tmp[MAXW];
    int i;
    if (m <= 1) {
        i = m;
        int n = S->n[i];
        for (int k = 0; k < n; k++) T->w[i][k] = -S->w[i][n - 1 - k];
        T->n[i] = n;
    } else if (m <= 5) {
        i = m <= 3 ? 0 : 1;
        int j = 1 - i, nj = S->n[j];
        if (m == 2 || m == 4)
            memcpy(tmp, S->w[j], nj);
        else
            for (int k = 0; k < nj; k++) tmp[k] = -S->w[j][nj - 1 - k];
        memcpy(T->w[i], S->w[i], S->n[i]);
        int r = join_into(T->w[i], S->n[i], tmp, nj);
        if (r < 0) return 0;
        T->n[i] = r;
    } else {
        i = m < 10 ? 0 : 1;
        let g = GEN[(m - 6) % 4], h = -g;
        const let *w = S->w[i];
        let *o = T->w[i];
        int n = S->n[i], k;
        if (n > 0 && w[0] == h) {                       /* g w: the g cancels */
            memcpy(o, w + 1, n - 1);
            k = n - 1;
        } else {
            if (n + 1 > MAXW) return 0;
            o[0] = g;
            memcpy(o + 1, w, n);
            k = n + 1;
        }
        if (k > 0 && o[k - 1] == g) {                   /* (g w) g^-1: the g^-1 cancels */
            k--;
        } else {
            if (k + 1 > MAXW) return 0;
            o[k++] = h;
        }
        T->n[i] = k;
    }
    int o = 1 - i;
    T->n[o] = S->n[o];
    memcpy(T->w[o], S->w[o], S->n[o]);
    return 1;
}

static uint64_t hash_state(const State *S) {
    uint64_t h = 0x9E3779B97F4A7C15ULL;
    for (int i = 0; i < 2; i++) {
        h ^= (uint64_t)(S->n[i] + 1) * 0xBF58476D1CE4E5B9ULL;
        h *= 0x94D049BB133111EBULL;
        for (int k = 0; k < S->n[i]; k++) {
            h ^= (uint64_t)(uint8_t)(S->w[i][k] + 3);
            h *= 0x100000001B3ULL;
        }
        h ^= h >> 29;
    }
    h ^= h >> 32;
    return h ? h : 1;
}

/* ---------- the table: hash -> (j, d2) with j - d2 largest ---------- */

static uint64_t *tkeys;
static int32_t *tval_j;
static int8_t *tval_d;
static int64_t tsize, tcap, tcount;

static int table_reset(int64_t want) {
    int64_t size = 1024;
    while (size < 2 * want) size <<= 1;
    if (size > tcap) {
        free(tkeys);
        free(tval_j);
        free(tval_d);
        tkeys = malloc(sizeof(uint64_t) * (size_t)size);
        tval_j = malloc(sizeof(int32_t) * (size_t)size);
        tval_d = malloc((size_t)size);
        if (!tkeys || !tval_j || !tval_d) {
            tcap = 0;
            return 0;
        }
        tcap = size;
    }
    tsize = size;
    tcount = 0;
    memset(tkeys, 0, sizeof(uint64_t) * (size_t)size);
    return 1;
}

static void table_put(uint64_t h, int j, int d) {
    uint64_t mask = (uint64_t)tsize - 1, p = h & mask;
    while (tkeys[p] && tkeys[p] != h) p = (p + 1) & mask;
    if (!tkeys[p]) {
        if (tcount * 10 >= tsize * 9) return;          /* never fill the table */
        tkeys[p] = h;
        tval_j[p] = j;
        tval_d[p] = (int8_t)d;
        tcount++;
    } else if (j - d > tval_j[p] - tval_d[p]) {
        tval_j[p] = j;
        tval_d[p] = (int8_t)d;
    }
}

static int table_get(uint64_t h, int *j, int *d) {
    uint64_t mask = (uint64_t)tsize - 1, p = h & mask;
    while (tkeys[p]) {
        if (tkeys[p] == h) {
            *j = tval_j[p];
            *d = tval_d[p];
            return 1;
        }
        p = (p + 1) & mask;
    }
    return 0;
}

/* ---------- the searches around one state ---------- */

enum { FILL, LOOKUP, FIND };

typedef struct {
    int mode;
    int centre;                 /* FILL: j; LOOKUP: i */
    int best_gain, best_j, best_d1, best_d2;
    int best_moves[MAXR];
    State best_t;
    const State *target;        /* FIND */
    int found_d, found_moves[MAXR];
} Ctx;

static State dfs_st[MAXR + 1];
static int dfs_mv[MAXR];
static Ctx ctx;

static void visit(Ctx *c, int depth) {
    const State *s = &dfs_st[depth];
    if (c->mode == FILL) {
        table_put(hash_state(s), c->centre, depth);
    } else if (c->mode == LOOKUP) {
        int j, d2;
        if (!table_get(hash_state(s), &j, &d2)) return;
        int gain = j - c->centre - depth - d2;
        if (gain > c->best_gain) {
            c->best_gain = gain;
            c->best_j = j;
            c->best_d1 = depth;
            c->best_d2 = d2;
            memcpy(c->best_moves, dfs_mv, sizeof(int) * (size_t)depth);
            copy_state(&c->best_t, s);
        }
    } else if ((c->found_d < 0 || depth < c->found_d) && same(s, c->target)) {
        c->found_d = depth;
        memcpy(c->found_moves, dfs_mv, sizeof(int) * (size_t)depth);
    }
}

/* every move sequence of length <= radius from dfs_st[0] that never undoes its last move */
static void dfs(Ctx *c, int depth, int radius, int prev) {
    visit(c, depth);
    if (depth == radius) return;
    for (int m = 0; m < 14; m++) {
        if (prev >= 0 && m == INV[prev]) continue;
        if (!apply_to(&dfs_st[depth], m, &dfs_st[depth + 1])) continue;
        dfs_mv[depth] = m;
        dfs(c, depth + 1, radius, m);
    }
}

static int64_t visits(int r) {                          /* a bound on the states dfs visits */
    int64_t v = 1, layer = 14;
    for (int k = 1; k <= r; k++) {
        v += layer;
        layer *= 13;
    }
    return v;
}

/* ---------- shortening ---------- */

static State *sts;
static int64_t sts_cap;

static int ensure_states(int n) {
    if (n + 1 > sts_cap) {
        free(sts);
        sts = malloc(sizeof(State) * (size_t)(n + 1));
        if (!sts) {
            sts_cap = 0;
            return 0;
        }
        sts_cap = n + 1;
    }
    return 1;
}

/* sts[0..n] := the states of path from S; 0 if a relator would pass MAXW */
static int states_of(const State *S, const int *path, int n) {
    copy_state(&sts[0], S);
    for (int k = 0; k < n; k++)
        if (path[k] < 0 || path[k] > 13 || !apply_to(&sts[k], path[k], &sts[k + 1])) return 0;
    return 1;
}

/* one round on path[0..n), its states in sts; the new path goes to out; its length, or -1 */
static int one_round(const int *path, int n, int r1, int r2, int64_t max_entries, int *out) {
    while (r2 > 0 && (int64_t)(n + 1) * visits(r2) > max_entries) r2--;
    if (!table_reset((int64_t)(n + 1) * visits(r2))) return -1;
    ctx.mode = FILL;
    for (int j = 0; j <= n; j++) {
        ctx.centre = j;
        copy_state(&dfs_st[0], &sts[j]);
        dfs(&ctx, 0, r2, -1);
    }
    int m = 0, i = 0;
    while (i < n) {
        ctx.mode = LOOKUP;
        ctx.centre = i;
        ctx.best_gain = 0;
        copy_state(&dfs_st[0], &sts[i]);
        dfs(&ctx, 0, r1, -1);
        if (ctx.best_gain > 0) {
            int j = ctx.best_j, d1 = ctx.best_d1, seq[2 * MAXR], k = 0;
            for (int t = 0; t < d1; t++) seq[k++] = ctx.best_moves[t];
            ctx.mode = FIND;
            ctx.target = &ctx.best_t;
            ctx.found_d = -1;
            copy_state(&dfs_st[0], &sts[j]);
            dfs(&ctx, 0, ctx.best_d2, -1);
            int ok = ctx.found_d >= 0 && j - i > d1 + ctx.found_d;
            if (ok) {
                for (int t = ctx.found_d - 1; t >= 0; t--) seq[k++] = INV[ctx.found_moves[t]];
                State *a = &dfs_st[0], *b = &dfs_st[1], *x;
                copy_state(a, &sts[i]);
                for (int t = 0; t < k && ok; t++) {
                    ok = apply_to(a, seq[t], b);
                    x = a;
                    a = b;
                    b = x;
                }
                ok = ok && same(a, &sts[j]);
            }
            if (ok) {
                for (int t = 0; t < k; t++) out[m++] = seq[t];
                i = j;
                continue;
            }
        }
        out[m++] = path[i++];
    }
    return m;
}

/* shorten path[0..n) from S in place; the new length, or -1 (a relator too long, no memory) */
static int shorten(const State *S, int *path, int n, int r1, int r2, int rounds,
                   int64_t max_entries, int *rounds_done, int *tmp) {
    int done = 0;
    if (!ensure_states(n)) return -1;
    while (done < rounds) {
        if (!states_of(S, path, n)) return -1;
        int m = one_round(path, n, r1, r2, max_entries, tmp);
        if (m < 0) return -1;
        done++;
        if (m >= n) break;
        memcpy(path, tmp, sizeof(int) * (size_t)m);
        n = m;
    }
    *rounds_done = done;
    return n;
}

/* the state at the end of path from S into F; 0 if a relator would pass MAXW or a move is bad */
static int end_state(const State *S, const int *path, int n, State *F) {
    State *a = &dfs_st[0], *b = &dfs_st[1], *x;
    copy_state(a, S);
    for (int k = 0; k < n; k++) {
        if (path[k] < 0 || path[k] > 13 || !apply_to(a, path[k], b)) return 0;
        x = a;
        a = b;
        b = x;
    }
    copy_state(F, a);
    return 1;
}

/* ---------- the self-test ---------- */

static uint64_t rng = 88172645463325252ULL;

static uint64_t xs(void) {
    rng ^= rng << 13;
    rng ^= rng >> 7;
    rng ^= rng << 17;
    return rng;
}

static void random_state(State *S, int maxlen) {
    for (int i = 0; i < 2; i++) {
        int n = 1 + (int)(xs() % (uint64_t)maxlen), k = 0;
        while (k < n) {
            let a = GEN[xs() % 4];
            if (k && S->w[i][k - 1] == -a) continue;
            S->w[i][k++] = a;
        }
        S->n[i] = n;
    }
}

/* random moves that keep the total length at most 80 (inversions always do) */
static void random_path(const State *S, int n, int *path) {
    static State a, b;
    copy_state(&a, S);
    for (int k = 0; k < n; k++) {
        int m;
        do m = (int)(xs() % 14); while (!apply_to(&a, m, &b) || b.n[0] + b.n[1] > 80);
        path[k] = m;
        copy_state(&a, &b);
    }
}

static int path_a[MAXN], path_b[MAXN], path_t[MAXN];

static int selftest(void) {
    static State S, T, U, F, G;
    int bad_inverse = 0, bad_loop = 0, bad_detour = 0, bad_end = 0, trials = 0;
    for (int t = 0; t < 300; t++) {                     /* every move is undone by INV */
        random_state(&S, 20);
        for (int m = 0; m < 14; m++) {
            if (!apply_to(&S, m, &T) || !apply_to(&T, INV[m], &U) || !same(&S, &U)) bad_inverse++;
        }
    }
    for (int t = 0; t < 60; t++) {                      /* P then P undone: a loop, cut to nothing */
        random_state(&S, 12);
        random_path(&S, 25, path_a);
        for (int k = 0; k < 25; k++) path_a[25 + k] = INV[path_a[24 - k]];
        int r, n = shorten(&S, path_a, 50, 3, 3, 8, 4000000, &r, path_t);
        if (n != 0) bad_loop++;
        trials++;
    }
    for (int t = 0; t < 60; t++) {                      /* a detour of two moves, cut */
        random_state(&S, 12);
        random_path(&S, 30, path_a);
        int k = 0;
        for (int q = 0; q < 15; q++) path_b[k++] = path_a[q];
        path_b[k++] = 6;
        path_b[k++] = 7;
        for (int q = 15; q < 30; q++) path_b[k++] = path_a[q];
        if (!end_state(&S, path_a, 30, &F)) {
            bad_end++;
            continue;
        }
        int r, n = shorten(&S, path_b, 32, 3, 3, 8, 4000000, &r, path_t);
        if (n < 0 || n > 30) bad_detour++;
        if (n < 0 || !end_state(&S, path_b, n, &G) || !same(&F, &G)) bad_end++;
        trials++;
    }
    for (int t = 0; t < 20; t++) {                      /* a random path keeps its end state */
        random_state(&S, 12);
        random_path(&S, 300, path_a);
        if (!end_state(&S, path_a, 300, &F)) {
            bad_end++;
            continue;
        }
        int r, n = shorten(&S, path_a, 300, 3, 3, 8, 4000000, &r, path_t);
        if (n < 0 || n > 300 || !end_state(&S, path_a, n, &G) || !same(&F, &G)) bad_end++;
        trials++;
    }
    int ok = !bad_inverse && !bad_loop && !bad_detour && !bad_end;
    printf("SELFTEST %s trials %d bad_inverse %d bad_loop %d bad_detour %d bad_end %d\n",
           ok ? "ok" : "FAIL", trials, bad_inverse, bad_loop, bad_detour, bad_end);
    return ok ? 0 : 1;
}

/* ---------- input and output ---------- */

static int parse_word(const char *s, State *S, int i) {    /* 0 if too long or a bad letter */
    int n = 0;
    if (!strcmp(s, "-")) {
        S->n[i] = 0;
        return 1;
    }
    for (; *s; s++) {
        let a = *s == 'x' ? 1 : *s == 'X' ? -1 : *s == 'y' ? 2 : *s == 'Y' ? -2 : 0;
        if (!a) return 0;
        if (n && S->w[i][n - 1] == -a) {
            n--;
        } else {
            if (n >= MAXW) return 0;
            S->w[i][n++] = a;
        }
    }
    S->n[i] = n;
    return 1;
}

static int parse_path(char *s, int *path) {               /* -1 if too long or a bad move */
    int n = 0;
    if (!strcmp(s, "-")) return 0;
    for (char *tok = strtok(s, ","); tok; tok = strtok(NULL, ",")) {
        char *end;
        long m = strtol(tok, &end, 10);
        if (*end || m < 0 || m > 13 || n >= MAXN) return -1;
        path[n++] = (int)m;
    }
    return n;
}

static void print_path(const int *path, int n) {
    if (n == 0) {
        printf("-\n");
        return;
    }
    for (int t = 0; t < n; t++) printf(t ? ",%d" : "%d", path[t]);
    printf("\n");
}

int main(int argc, char **argv) {
    int r1 = 3, r2 = 3, rounds = 8, self = 0;
    int64_t max_entries = 4000000;
    for (int k = 1; k < argc; k++) {
        if (!strcmp(argv[k], "--selftest")) self = 1;
        else if (k + 1 < argc && !strcmp(argv[k], "--r1")) r1 = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--r2")) r2 = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--rounds")) rounds = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--max-entries")) max_entries = atoll(argv[++k]);
        else {
            fprintf(stderr, "unknown argument %s\n", argv[k]);
            return 2;
        }
    }
    if (r1 < 0 || r1 > MAXR || r2 < 0 || r2 > MAXR) {
        fprintf(stderr, "radius out of range\n");
        return 2;
    }
    if (self) return selftest();
    char *line = NULL, *orig = NULL;
    size_t cap = 0, ocap = 0;
    ssize_t len;
    static State S, F, G;
    while ((len = getline(&line, &cap, stdin)) > 0) {
        if ((size_t)len + 1 > ocap) {
            free(orig);
            ocap = (size_t)len + 1;
            orig = malloc(ocap);
            if (!orig) return 3;
        }
        char *id = strtok(line, " \t\r\n"), *a = strtok(NULL, " \t\r\n");
        char *b = strtok(NULL, " \t\r\n"), *p = strtok(NULL, " \t\r\n");
        if (!id || !a || !b || !p) continue;
        strcpy(orig, p);
        double t0 = now();
        int n = -1, m = -1, r = 0;
        const char *status = "LONG";
        if (parse_word(a, &S, 0) && parse_word(b, &S, 1)) n = parse_path(p, path_a);
        if (n < 0) {
            status = "ERROR";
        } else if (end_state(&S, path_a, n, &F)) {
            memcpy(path_b, path_a, sizeof(int) * (size_t)n);
            m = shorten(&S, path_b, n, r1, r2, rounds, max_entries, &r, path_t);
            if (m >= 0)
                status = end_state(&S, path_b, m, &G) && same(&F, &G) && m <= n ? "OK" : "ERROR";
        }
        int good = !strcmp(status, "OK");
        printf("%s %s %d %d %d %.3f ", id, status, n, good ? m : n, r, now() - t0);
        if (good) {
            print_path(path_b, m);
        } else {
            printf("%s\n", orig);
        }
        fflush(stdout);
    }
    free(line);
    free(orig);
    return 0;
}
