# Results page rules

These rules apply to both result pages of the results app: `planning.html` and `platform.html`. They come from rehearsed live runs and keep the pages readable on a projector and honest about what is known.

## Editing the app

- The app is built by `assets/results-app/build_app.py`. Do not start a server, open a browser or rebuild the app unless the user asks.
- Change only the result page the step owns. Leave `index.html`, `use-cases.html` and `assets/` unchanged.
- Keep `<head>`, `<header>` and `<footer>` of the page exactly as built. Replace only the `<main>` element.
- Remove the line `<meta http-equiv="refresh" content="5">` once the page has content.
- Use the classes in `assets/app.css`: `.cards`, `.card.a` to `.card.d` (one per case, in case order), `.tag`, `.open`, `.lead`, tables. Extra styles go into one `<style>` block in the page's `<head>`.
- Diagrams are inline SVG. Nothing is loaded from the internet.
- Never say a page was written unless the file was written.

## Colours

| Use | Colour |
|---|---|
| Case A | `#1e4e8c` on `#e8f0fb` |
| Case B | `#8a4b00` on `#fdf1e2` |
| Case C | `#1f6f43` on `#e6f4ec` |
| Case D | `#6b2c91` on `#f3e9f9` |
| Shared or neutral parts | `#4a5568` on `#edf2f7` |
| Unknown or open items | `#b42318`, bold |

## Sizes and layout

- Body text at least 22px. Diagram labels at least 16px in dark colours.
- Content fits a 16:9 screen width. Keep table cells short.

## Diagrams

- White background.
- Every relationship is a line with an arrowhead from source to target.
- No overlapping labels. Lines do not cross through labels.
- Every component that runs somewhere is drawn on what it runs on.
- A short caption under the diagram explains the colours.

## Writing

- Write for the audience the user names. Without one, write for decision makers who are not cloud specialists, like a short briefing.
- Each page opens with one sentence that states its main finding about the cases.
- Use the established terms (IaaS, project, virtual machine, Kubernetes cluster, GPU) and explain each once in a few words. Do not invent substitute phrases.
- Do not recommend a provider or a product.
- No statements about the page or the process: no references to other pages, no "nothing was built or tested", no list of skills used, no disclaimers. Execution and evidence status go into the chat reply only.
- Show each unknown once, as an unknown, in the open-item colour. Never fill it with an assumed value.
