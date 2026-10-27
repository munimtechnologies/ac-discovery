# acc02 results (counts only, no paths)

MV2 of Munim, Inc., 2026-10-27. Made with AI agents working in MV2's name. Text CC BY 4.0.

Four shards (index mod 4 of the 10,115 scored presentations), each with the build, acc02.c's
self-test, the 424 training presentations as a control, both search passes, the verifier on every
path, and the grade. Every graded check held in all four (16 each).

    shard  host   scored  solved  pass A  pass B  median length  longest  minutes  peak GB
    a      Dell   2,529   1,184   872     312     280            3,502    68       0.42
    b      Dell   2,529   1,192   845     347     273            4,052    69       0.40
    c      Blade  2,529   1,316   876     440     292            4,765    62       0.54
    d      Blade  2,528   1,242   856     386     299            3,900    66       0.54
    all           10,115  4,934   3,449   1,485

Training: 424 of 424 solved in every shard, every path accepted with the training manifest.

Solved by starting total length (from the rows; denominators counted from them as well):

    start total   solved / presentations
    at most 20    487 / 1,342   (36.3%)
    21 to 29      2,270 / 4,772 (47.6%)
    30 or more    2,177 / 4,001 (54.4%)

Graded against acc02-predictions.md: every check held (65%): held. Training at least 418 (70%):
held. Scored at least 5% (70%), 15% (45%), 30% (25%): held; at least 50% (8%): missed (48.8%).
Pass A ahead of pass B (70%): held. Median length over 60 (60%): held. Small presentations solved
more often than large ones (85%): missed, the other way round. Shards within 240 minutes and under
1.2 GB (85%): held.
