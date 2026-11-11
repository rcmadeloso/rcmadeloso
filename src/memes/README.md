# Meme slots

One file per picture spot on the profile. The files here now are the same cleaned-up
internet templates the portfolio uses, kept as placeholders. To swap one, save the new
picture under the **same file name**, run `python3 build.py` in the repo root, and commit.

## Slots

| File | Shows in | Placeholder now | Caption it sits with | Box on the page |
| --- | --- | --- | --- | --- |
| `ship-1-plan.png` | How I ship in 2026, panel 1 | Wojak (Feels Guy), calm | "I write the plan and the guardrails." | 320 x 176 |
| `ship-2-build.png` | How I ship in 2026, panel 2 | LOL Guy, laughing | "Agents build it with my custom skills." | 320 x 176 |
| `ship-3-review.png` | How I ship in 2026, panel 3 | Y U No, arms up, furious | "Reviewer agents try to break it." and the shout "Y U NO PASS" | 320 x 176 |
| `ship-4-ship.png` | How I ship in 2026, panel 4 | Aww Yeah, head back, laughing | "I verify, test and ship." and the shout "SHIP IT" | 320 x 176 |
| `say-hi.png` | Say hi | Y U No, arms up, furious | "Y U NO" above, "SEND ME AN EMAIL" below | 194 x 164 |
| `../portrait.png` | The hero window | Your own portrait, not a placeholder | "WHEN THE CLIENT SAYS" above, "IT'S JUST A SMALL CHANGE" below | 344 x 344, square |

## How to make a replacement

- Black line art on a white or transparent background. PNG.
- Any shape works: the picture is fitted and centred in its box, never cropped or stretched.
  A shape close to the box fills it best. The portrait is the exception: keep it square.
- Draw at twice the box size or more, so it stays sharp on high-density screens.
- No text inside the picture. Captions are set by `build.py`.
- In panels 3 and 4 the shout covers the bottom fifth of the picture, and in Say hi the two
  captions cover its top and bottom edges. Keep the face clear of those bands.
- Keep the pose and expression, so the caption still lands.
