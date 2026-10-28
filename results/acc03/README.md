# acc03 results (counts only, no paths)

MV2 of Munim, Inc., 2026-10-27/28. Made with AI agents working in MV2's name. Text CC BY 4.0.

All four shards have finished. Every graded check held in every shard (18 of 18 each): the build
and both C self-tests, the 424 training presentations as a control, the three search passes, the
shortener, acc01's replay of every shortened path, and the challenge's verifier on every path as AC
and as Stable AC, with the official manifest, at the length the verifier reports.

    shard  host   scored  solved  pass A  pass B  pass C  acc02 solved  minutes  peak GB
    a      Dell   2,529   1,393   873     322     198     1,184         185      0.92
    b      Blade  2,529   1,469   877     477     115     1,192         169      1.04
    c      Blade  2,529   1,455   872     441     142     1,316         168      1.04
    d      Blade  2,528   1,399   861     394     144     1,242         172      1.04
    all           10,115  5,716   3,483   1,634   599     4,934

acc03 solved 5,716 of the 10,115 scored presentations (56.5%), 782 more than acc02's 4,934.

Path lengths before and after the shortener (the same paths, solved presentations only):

    shard  median before  median after  total before  total after  shorter          longest after
    a      303            212           621,267       424,488      1,389 of 1,393   2,972
    b      306            218           692,728       476,524      1,464 of 1,469   3,509
    c      311            222           672,818       463,037      1,451 of 1,455   3,945
    d      331            234           674,753       462,453      1,394 of 1,399   4,004
    all                                 2,661,566     1,826,502    5,698 of 5,716

The shortener cut the total length by 31.4% (31.2% to 31.7% by shard), and the median by 29% to
30%. On the 424 training presentations it cut the total from 11,019 to 8,047 moves (median 20 to
14). Time per shard: passes A, B and C took 949, 2,927 and 6,396 s (a), 905, 2,830 and 5,407 s (b),
882, 2,718 and 5,564 s (c) and 889, 2,837 and 5,786 s (d); shortening took 685, 759, 745 and 699 s.

Solved by starting total length:

    start total   a             b             c             d             all
    at most 20    132 / 342     124 / 322     129 / 332     130 / 346     515 / 1,342   (38.4%)
    21 to 29      633 / 1,180   695 / 1,213   649 / 1,170   659 / 1,209   2,636 / 4,772 (55.2%)
    30 or more    628 / 1,007   650 / 994     677 / 1,027   610 / 973     2,565 / 4,001 (64.1%)

Graded against acc03-predictions.md, on all four shards: every check held in every shard (70%):
held. Solved at least acc02's 4,934 (75%): held (5,716). Pass C at least 5% of what A and B leave
(55%): held (599 of 4,998, 12.0%; 9.8% to 14.8% by shard); at least 15% (20%): missed. Median after
shortening at most two thirds of before (60%): missed (0.70 to 0.71 in every shard); at most half
(35%): missed. Total length cut by at least 25% (60%): held. At least 90% strictly shorter (75%):
held (99.7%). Start total 30 or more solved more often than 20 or less (80%): held in every shard.
Each shard within 240 minutes (70%) and under 1.8 GB (80%): held.

Only the shortest verified path on a presentation scores in the Discovery Track, so a 30% cut
matters only where another team's path is not shorter still. Job acc04 (acc04-predictions.md)
measures what larger shortcut radii add before any bulk run. These counts say nothing about the
Andrews-Curtis conjecture itself, which remains open.
