/* Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0). */
/*
 * acc06.c: job acc06's beam search for the SAIR / Caltech Andrews-Curtis Conjecture Challenge
 * (Discovery Track), predictions in acc06-predictions.md, written before the job ran.
 *
 * Only the shortest verified path on a presentation scores, and its length is the number of the
 * verifier's moves. acc02.c ranks pairs of relators taken up to rotation, so the conjugations that
 * rotate them are paid for afterwards, and acc03.c can only cut detours locally. acc06 searches the
 * verifier's own moves level by level, so a path found at level L has exactly L moves:
 *
 *     level 0 is the presentation; level k + 1 is every state one move from a state kept at level
 *     k, with no empty relator, total relator length at most the start's plus --slack, and not kept
 *     at an earlier level; of these the --width with the smallest total length are kept (ties: in
 *     the order generated, so children of shorter parents first).
 *
 * Every new state is looked up in the target's ball (every state within --ball moves of (x, y), by
 * breadth-first search): a state at level k and distance d gives a path of length k + d, and the
 * search stops once k + 1 reaches the best length found, after --max-depth levels or after
 * --seconds. The path is replayed from the presentation and must end at exactly (x, y) with the
 * length found (status ERROR otherwise). States are keyed by 64-bit hashes, so a collision can only
 * drop a state or a ball entry (the finish is followed and checked move by move), never produce a
 * wrong path.
 *
 * Moves are the verifier's (ac-r2-v1, as acc01.py and acc03.c): 0, 1 invert r0, r1; 2 to 5 are
 * r0 -> r0 r1, r0 r1^-1 and r1 -> r1 r0, r1 r0^-1; 6 to 9 conjugate r0 and 10 to 13 conjugate r1 by
 * x, x^-1, y, y^-1 (r -> g r g^-1). Move m is undone by INV[m].
 *
 * Input lines: "<id> <r0> <r1>", words over x X y Y (X = x^-1, Y = y^-1).
 * Output lines: "<id> <SOLVED|NONE|SKIP|ERROR> <length> <levels> <seconds> <path>", the path
 * comma-separated ("-" if none).
 *
 * Usage: acc06 [--width B] [--slack K] [--max-depth D] [--seconds S] [--ball R]
 *        acc06 --selftest
 */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <time.h>

#define MAXW 96                 /* longest relator a state may hold */
#define MAXT (2 * MAXW)         /* longest total */
#define MAXPATH 100000          /* the verifier's move limit */
#define MAXFIN 16               /* longest finish taken from the ball */

typedef signed char let;

typedef struct { int n[2]; let w[2][MAXW]; } State;

static const int INV[14] = {0, 1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12};
static const let GEN[4] = {1, -1, 2, -2};

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

/* ---------- words, states and the moves (as acc03.c) ---------- */

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

/* ---------- the target's ball: hash -> (distance, move one step closer) ---------- */

static State target;
static uint64_t *bkeys;
static int8_t *bdist, *bstep;
static int64_t bsize, bcount;

static int64_t ball_find(uint64_t h) {                     /* the slot of h, or -1 */
    uint64_t mask = (uint64_t)bsize - 1, p = h & mask;
    while (bkeys[p]) {
        if (bkeys[p] == h) return (int64_t)p;
        p = (p + 1) & mask;
    }
    return -1;
}

static int ball_add(uint64_t h, int d, int step) {        /* 1 if h was new and was stored */
    uint64_t mask = (uint64_t)bsize - 1, p = h & mask;
    while (bkeys[p]) {
        if (bkeys[p] == h) return 0;
        p = (p + 1) & mask;
    }
    if (bcount * 4 >= bsize * 3) return 0;              /* never fill the table */
    bkeys[p] = h;
    bdist[p] = (int8_t)d;
    bstep[p] = (int8_t)step;
    bcount++;
    return 1;
}

static int64_t layer_bound(int d) {                        /* states at distance d: <= 14 * 13^(d-1) */
    int64_t v = 1;
    for (int k = 1; k <= d; k++) v *= k == 1 ? 14 : 13;
    return v;
}

static int build_ball(int radius) {
    target.n[0] = target.n[1] = 1;
    target.w[0][0] = 1;
    target.w[1][0] = 2;
    int64_t all = 0;
    for (int d = 0; d <= radius; d++) all += layer_bound(d);
    bsize = 1024;
    while (bsize < 2 * all) bsize <<= 1;
    bkeys = calloc((size_t)bsize, sizeof(uint64_t));
    bdist = malloc((size_t)bsize);
    bstep = malloc((size_t)bsize);
    int64_t cap = radius >= 2 ? layer_bound(radius - 1) : 1;
    State *a = malloc(sizeof(State) * (size_t)cap), *b = malloc(sizeof(State) * (size_t)cap), *x;
    if (!bkeys || !bdist || !bstep || !a || !b) return 0;
    copy_state(&a[0], &target);
    int64_t na = 1;
    ball_add(hash_state(&target), 0, -1);
    for (int d = 1; d <= radius; d++) {
        int64_t nb = 0;
        for (int64_t k = 0; k < na; k++) {
            for (int m = 0; m < 14; m++) {
                State t;
                if (!apply_to(&a[k], m, &t)) continue;
                if (!ball_add(hash_state(&t), d, INV[m])) continue;
                if (d < radius && nb < cap) copy_state(&b[nb++], &t);
            }
        }
        x = a;
        a = b;
        b = x;
        na = nb;
    }
    free(a);
    free(b);
    return 1;
}

/* the ball's moves from s to the target into out; their number, or -1 (not in the ball, a loop,
 * or a collision: the end must be exactly the target) */
static int finish(const State *s, int *out) {
    State a, b;
    copy_state(&a, s);
    int n = 0;
    for (;;) {
        int64_t p = ball_find(hash_state(&a));
        if (p < 0) return -1;
        if (bdist[p] == 0) return same(&a, &target) ? n : -1;
        if (n >= MAXFIN) return -1;
        int m = bstep[p];
        if (m < 0 || !apply_to(&a, m, &b)) return -1;
        out[n++] = m;
        copy_state(&a, &b);
    }
}

/* ---------- the beam ---------- */

static int64_t width = 4000, max_depth = 400;
static int slack = 24, ball_r = 5;
static double max_seconds = 20.0;

static State *cur, *kid;                /* the states kept at this level; their children */
static int32_t *cur_link, *kid_par, *order;
static uint8_t *kid_mv;
static uint64_t *kid_h;
static int16_t *kid_tot;
static int32_t *lk_par;                 /* links: the kept states of every level, as a tree */
static uint8_t *lk_mv;
static int64_t lk_cap, lk_n;
static uint64_t *vkeys;                 /* hashes of every kept state */
static int64_t vsize, vcount;
static uint64_t *lkeys;                 /* hashes of this level's children (lstamp == stamp) */
static uint32_t *lstamp, stamp;
static int64_t lsize;

static int vhas(uint64_t h) {
    uint64_t mask = (uint64_t)vsize - 1, p = h & mask;
    while (vkeys[p]) {
        if (vkeys[p] == h) return 1;
        p = (p + 1) & mask;
    }
    return 0;
}

static void vadd(uint64_t h) {
    uint64_t mask = (uint64_t)vsize - 1, p = h & mask;
    while (vkeys[p]) {
        if (vkeys[p] == h) return;
        p = (p + 1) & mask;
    }
    if (vcount * 4 >= vsize * 3) return;                /* full: later levels just dedupe less */
    vkeys[p] = h;
    vcount++;
}

static int ladd(uint64_t h) {                              /* 1 if h is new at this level */
    uint64_t mask = (uint64_t)lsize - 1, p = h & mask;
    while (lstamp[p] == stamp) {
        if (lkeys[p] == h) return 0;
        p = (p + 1) & mask;
    }
    lkeys[p] = h;
    lstamp[p] = stamp;
    return 1;
}

static int alloc_beam(void) {
    int64_t nk = width * 14;
    lk_cap = width * max_depth + 1;
    int64_t want = lk_cap < ((int64_t)1 << 23) ? lk_cap : ((int64_t)1 << 23);
    vsize = 1024;
    while (vsize < 2 * want) vsize <<= 1;
    lsize = 1024;
    while (lsize < 2 * nk) lsize <<= 1;
    cur = malloc(sizeof(State) * (size_t)width);
    kid = malloc(sizeof(State) * (size_t)nk);
    cur_link = malloc(sizeof(int32_t) * (size_t)width);
    kid_par = malloc(sizeof(int32_t) * (size_t)nk);
    order = malloc(sizeof(int32_t) * (size_t)nk);
    kid_mv = malloc((size_t)nk);
    kid_h = malloc(sizeof(uint64_t) * (size_t)nk);
    kid_tot = malloc(sizeof(int16_t) * (size_t)nk);
    lk_par = malloc(sizeof(int32_t) * (size_t)lk_cap);
    lk_mv = malloc((size_t)lk_cap);
    vkeys = malloc(sizeof(uint64_t) * (size_t)vsize);
    lkeys = malloc(sizeof(uint64_t) * (size_t)lsize);
    lstamp = calloc((size_t)lsize, sizeof(uint32_t));
    return cur && kid && cur_link && kid_par && order && kid_mv && kid_h && kid_tot && lk_par
           && lk_mv && vkeys && lkeys && lstamp && lk_cap < INT32_MAX;
}

enum { SOLVED = 1, NONE = 0, SKIP = -1, ERROR = -2 };

static int path[MAXPATH + MAXFIN + 1];
static int path_n;

/* the beam from S; on SOLVED, path[0..path_n) takes S to exactly the target */
static int search(const State *S, double t0, int *levels_out) {
    int fin[MAXFIN];
    int cap = S->n[0] + S->n[1] + slack;
    if (cap > MAXT) cap = MAXT;
    path_n = 0;
    *levels_out = 0;
    if (S->n[0] == 0 || S->n[1] == 0) return SKIP;
    memset(vkeys, 0, sizeof(uint64_t) * (size_t)vsize);
    vcount = 0;
    lk_par[0] = -1;
    lk_mv[0] = 0;
    lk_n = 1;
    copy_state(&cur[0], S);
    cur_link[0] = 0;
    int64_t nc = 1;
    vadd(hash_state(S));
    int best = -1, best_mv = -1;
    int32_t best_link = -1;
    State best_state;
    if (ball_find(hash_state(S)) >= 0) {
        int f = finish(S, fin);
        if (f >= 0) {
            best = f;
            best_link = 0;
            copy_state(&best_state, S);
        }
    }
    int64_t depth;
    for (depth = 0; depth < max_depth; depth++) {
        if (best >= 0 && depth + 1 >= best) break;
        if (now() - t0 > max_seconds) break;
        stamp++;
        int64_t nk = 0, count[MAXT + 1];
        memset(count, 0, sizeof count);
        for (int64_t b = 0; b < nc; b++) {
            for (int m = 0; m < 14; m++) {
                State *t = &kid[nk];
                if (!apply_to(&cur[b], m, t)) continue;
                int tot = t->n[0] + t->n[1];
                if (tot > cap || t->n[0] == 0 || t->n[1] == 0) continue;
                uint64_t h = hash_state(t);
                if (vhas(h) || !ladd(h)) continue;
                int64_t q = ball_find(h);
                if (q >= 0 && (best < 0 || depth + 1 + bdist[q] < best)) {
                    int f = finish(t, fin);
                    if (f == bdist[q]) {
                        best = (int)depth + 1 + f;
                        best_link = cur_link[b];
                        best_mv = m;
                        copy_state(&best_state, t);
                    }
                }
                kid_par[nk] = cur_link[b];
                kid_mv[nk] = (uint8_t)m;
                kid_h[nk] = h;
                kid_tot[nk] = (int16_t)tot;
                count[tot]++;
                nk++;
            }
        }
        if (nk == 0) break;
        /* the `width` children with the smallest totals, in the order generated within a total */
        int64_t pos = 0;
        for (int t = 0; t <= MAXT; t++) {
            int64_t c = count[t];
            count[t] = pos;
            pos += c;
        }
        for (int64_t k = 0; k < nk; k++) order[count[kid_tot[k]]++] = (int32_t)k;
        int64_t keep = nk < width ? nk : width;
        if (lk_n + keep > lk_cap) break;
        for (int64_t k = 0; k < keep; k++) {
            int64_t c = order[k];
            copy_state(&cur[k], &kid[c]);
            cur_link[k] = (int32_t)lk_n;
            lk_par[lk_n] = kid_par[c];
            lk_mv[lk_n] = kid_mv[c];
            lk_n++;
            vadd(kid_h[c]);
        }
        nc = keep;
    }
    *levels_out = (int)depth;
    if (best < 0) return NONE;
    int len = 0;
    for (int32_t q = best_link; lk_par[q] >= 0; q = lk_par[q]) len++;
    if (len + 1 + MAXFIN > MAXPATH) return ERROR;
    int t = len;
    for (int32_t q = best_link; lk_par[q] >= 0; q = lk_par[q]) path[--t] = lk_mv[q];
    int n = len;
    if (best_mv >= 0) path[n++] = best_mv;
    int f = finish(&best_state, fin);
    if (f < 0) return ERROR;
    for (int k = 0; k < f; k++) path[n++] = fin[k];
    path_n = n;
    State a, b2;
    copy_state(&a, S);
    for (int k = 0; k < n; k++) {
        if (!apply_to(&a, path[k], &b2)) return ERROR;
        copy_state(&a, &b2);
    }
    return same(&a, &target) && n == best ? SOLVED : ERROR;
}

/* ---------- the self-test ---------- */

static uint64_t rng = 88172645463325252ULL;

static uint64_t xs(void) {
    rng ^= rng << 13;
    rng ^= rng >> 7;
    rng ^= rng << 17;
    return rng;
}

static int parse_word(const char *s, State *S, int i) {    /* 0 if too long or a bad letter */
    int n = 0;
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

static int selftest(void) {
    int bad_inverse = 0, bad_ball = 0, bad_near = 0, bad_far = 0, bad_given = 0, solved_far = 0;
    State S, T, U;
    if (max_depth > 80) max_depth = 80;                 /* the beam arrays were sized for more */
    if (max_seconds > 2.0) max_seconds = 2.0;
    for (int t = 0; t < 300; t++) {                     /* every move is undone by INV */
        for (int i = 0; i < 2; i++) {
            int n = 1 + (int)(xs() % 20), k = 0;
            while (k < n) {
                let a = GEN[xs() % 4];
                if (k && S.w[i][k - 1] == -a) continue;
                S.w[i][k++] = a;
            }
            S.n[i] = n;
        }
        for (int m = 0; m < 14; m++)
            if (!apply_to(&S, m, &T) || !apply_to(&T, INV[m], &U) || !same(&S, &U)) bad_inverse++;
    }
    int fin[MAXFIN];
    if (ball_find(hash_state(&target)) < 0 || finish(&target, fin) != 0) bad_ball++;
    for (int m = 0; m < 14; m++) {                      /* one move from the target: distance <= 1 */
        apply_to(&target, m, &T);
        int64_t p = ball_find(hash_state(&T));
        if (p < 0 || bdist[p] > 1 || finish(&T, fin) != bdist[p]) bad_ball++;
    }
    for (int t = 0; t < 200; t++) {                     /* scrambles of the target, k random moves */
        int k = 1 + (int)(xs() % 24);
        copy_state(&S, &target);
        for (int s = 0; s < k; s++) {
            int m;
            do m = (int)(xs() % 14);
            while (!apply_to(&S, m, &T) || T.n[0] == 0 || T.n[1] == 0 || T.n[0] + T.n[1] > 40);
            copy_state(&S, &T);
        }
        int levels, st = search(&S, now(), &levels);
        if (k <= ball_r) {                              /* inside the ball: solved at once, <= k */
            if (st != SOLVED || path_n > k) bad_near++;
        } else if (st == SOLVED) {
            solved_far++;
        } else if (st != NONE) {
            bad_far++;                                  /* ERROR or SKIP: never */
        }
    }
    /* presentations built from (x, y) by explicit moves (acc02.c's self-test) */
    static const char *Q[][2] = {{"xy", "y"}, {"xyx", "yx"}, {"yx", "yxy"}, {"xyxYX", "xy"},
                                 {"xyxYX", "xyxyXYX"}};
    for (size_t k = 0; k < sizeof Q / sizeof Q[0]; k++) {
        if (!parse_word(Q[k][0], &S, 0) || !parse_word(Q[k][1], &S, 1)) {
            bad_given++;
            continue;
        }
        int levels;
        if (search(&S, now(), &levels) != SOLVED) bad_given++;
    }
    int ok = !bad_inverse && !bad_ball && !bad_near && !bad_far && !bad_given && solved_far > 0;
    printf("SELFTEST %s ball %lld bad_inverse %d bad_ball %d bad_near %d bad_far %d bad_given %d "
           "solved_far %d\n", ok ? "ok" : "FAIL", (long long)bcount, bad_inverse, bad_ball,
           bad_near, bad_far, bad_given, solved_far);
    return ok ? 0 : 1;
}

/* ---------- input and output ---------- */

int main(int argc, char **argv) {
    int self = 0;
    for (int k = 1; k < argc; k++) {
        if (!strcmp(argv[k], "--selftest")) self = 1;
        else if (k + 1 < argc && !strcmp(argv[k], "--width")) width = atoll(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--slack")) slack = atoi(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--max-depth")) max_depth = atoll(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--seconds")) max_seconds = atof(argv[++k]);
        else if (k + 1 < argc && !strcmp(argv[k], "--ball")) ball_r = atoi(argv[++k]);
        else {
            fprintf(stderr, "unknown argument %s\n", argv[k]);
            return 2;
        }
    }
    if (width < 1 || max_depth < 1 || slack < 0 || ball_r < 0 || ball_r > 6) {
        fprintf(stderr, "argument out of range\n");
        return 2;
    }
    if (!build_ball(ball_r) || !alloc_beam()) {
        fprintf(stderr, "out of memory\n");
        return 3;
    }
    if (self) return selftest();
    char *line = NULL;
    size_t lcap = 0;
    static State S;
    while (getline(&line, &lcap, stdin) > 0) {
        char *id = strtok(line, " \t\r\n"), *a = strtok(NULL, " \t\r\n");
        char *b = strtok(NULL, " \t\r\n");
        if (!id || !a || !b) continue;
        double t0 = now();
        int levels = 0, st;
        if (!parse_word(a, &S, 0) || !parse_word(b, &S, 1)) {
            st = SKIP;
            path_n = 0;
        } else {
            st = search(&S, t0, &levels);
        }
        const char *name = st == SOLVED ? "SOLVED" : st == NONE ? "NONE" : st == SKIP ? "SKIP"
                                                                                 : "ERROR";
        printf("%s %s %d %d %.3f ", id, name, st == SOLVED ? path_n : 0, levels, now() - t0);
        if (st == SOLVED && path_n > 0) {
            for (int t = 0; t < path_n; t++) printf(t ? ",%d" : "%d", path[t]);
            printf("\n");
        } else {
            printf("-\n");
        }
        fflush(stdout);
    }
    free(line);
    return 0;
}
