# Common Test Chinese Q4 reference spec (R8 / 2026)

This file records the **functional structure** used to constrain internal original-item generation. It is not a template for copying official content.

## Official reference points

- The 2026 Chinese examination has 50 answer numbers in total and Q4 is worth 60 points.
- In the 2026 main examination, Q4 spans answer numbers **21–36**, i.e. 16 answer slots.
- Q4 is divided into **A and B** within one continuing scenario.
- The official item-writing committee has described Q4 as assessing the ability to read necessary information from familiar, realistic materials, compare/judge multiple pieces of information, and organize/integrate content.
- Recent Q4s use heterogeneous materials such as conversations, tables, graphs, checklists/profiles and process/flow information rather than a single long passage.

## Internal abstraction

Do not reproduce the 2026 pet-related scenario or its distinctive material sequence. Preserve only the abstract assessment pattern:

```text
realistic purpose / situation
        ↓
A: receive and understand information
        ↓
structured information + comparison / integration
        ↓
scenario progresses
        ↓
B: use information for action / selection / decision
        ↓
condition matching / process following / integrated judgment
```

## Sources

- University Entrance Examination Center, R8 main examination questions:  
  https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_honshiken_mondai.html
- University Entrance Examination Center, R6 Chinese item-writing committee self-evaluation:  
  https://www.dnc.ac.jp/albums/abm.php?d=677&f=abm00004608.pdf&n=R6%E6%9C%AC%E8%A9%A6%E9%A8%93_%E4%B8%AD%E5%9B%BD%E8%AA%9E_%E8%87%AA%E5%B7%B1%E8%A9%95%E4%BE%A1.pdf

When a new examination year is adopted as the baseline, add a new version rather than silently editing historical assumptions.
