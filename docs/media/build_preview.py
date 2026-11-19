"""Build the illustrative README GIF and editable SVG. Optional dev dependency: Pillow."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = '#0b1218'
PANEL = '#13212b'
BORDER = '#2a3a46'
TEXT = '#f0f5f6'
MUTED = '#a8bbc7'
ACCENT = '#60e0be'
STAGES = ['Analyze', 'Plan', 'Fix', 'Test', 'Review', 'Draft PR']
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')


def font(size, bold=False, mono=False):
    name = 'DejaVuSansMono' if mono else 'DejaVuSans'
    return ImageFont.truetype(str(FONT_DIR / (name + ('-Bold' if bold else '') + '.ttf')), size)


def text(draw, pos, value, size=25, color=TEXT, bold=False, mono=False):
    draw.text(pos, value, font=font(size, bold, mono), fill=color)


def rounded(draw, bounds, fill=PANEL, outline=BORDER, radius=16, width=2):
    draw.rounded_rectangle(bounds, radius, fill=fill, outline=outline, width=width)


def centered(draw, cx, y, value, size=22, color=TEXT, bold=False):
    f = font(size, bold)
    draw.text((cx, y), value, font=f, fill=color, anchor='mt')


def arrow(draw, start, end, color=BORDER):
    draw.line([start, end], fill=color, width=3)
    x, y = end
    draw.line([(x - 8, y - 6), end, (x - 8, y + 6)], fill=color, width=3)


SCENES = [
    ('Start with the issue.', 'GitHub issues or local tickets. A clear source for every run.',
     None, 'ONE SHORT REQUEST', ['/doforme:endtoend #42', 'Example issue: a task is missing from the board.'], 2600),
    ('Understand what is broken.', 'Trace the reported behavior to source and confirmed requirements.',
     0, 'EVIDENCE BEFORE EDITS', ['Issue validity + root-cause hypotheses', 'Source locations, confidence, and open questions.'], 2300),
    ('Approve a concrete plan.', 'See the proposed files and test commands before a repair starts.',
     1, 'YOUR SCOPE DECISION', ['Files to change + commands to run', 'Approve, adjust, or pause for clarification.'], 2800),
    ('Make the scoped repair.', 'The fixer works within the files and commands you approved.',
     2, 'BOUNDED CHANGES', ['A focused diff + regression evidence', 'Observe the bug-related failure, then the repaired result.'], 2200),
    ('Verify the behavior.', 'A separate test stage checks the repair against acceptance criteria.',
     3, 'INDEPENDENT TESTING', ['Actual test results + AC coverage', 'Unrun checks and evidence gaps remain visible.'], 2200),
    ('Review the evidence.', 'Check the diff, reports, and tested content before preparing a draft.',
     4, 'A CHECKED HANDOFF', ['Review verdict + traceable findings', 'Proceed when the required review and evidence gates pass.'], 2200),
    ('Get a reviewable PR draft.', 'Bring the change summary, test evidence, and risks to your team.',
     5, 'LOCAL DRAFT READY FOR REVIEW', ['Change summary + tests + limitations', 'Publication, merge, and business acceptance follow your process.'], 2800),
    ('Close the loop with your team.', 'Review, CI, QA/UAT, and owner acceptance complete the lifecycle.',
     None, 'OPTIONAL TELEGRAM INTEGRATION', ['New-bug alerts → owner-attested resolution', 'Resolution alerts require the merged PR, checks, and owner evidence.'], 3000),
]


def frame(scene):
    headline, subtitle, active, label, lines, _ = scene
    im = Image.new('RGB', (1400, 760), BG)
    d = ImageDraw.Draw(im)
    text(d, (56, 36), 'doforme', 31, bold=True)
    text(d, (988, 47), 'CLAUDE CODE PLUGIN', 18, MUTED, mono=True)
    d.line([(56, 99), (1344, 99)], fill=BORDER, width=2)
    text(d, (56, 137), headline, 51, bold=True)
    text(d, (58, 218), subtitle, 25, MUTED)
    # A fixed timeline: motion highlights stages, never fabricated terminal output.
    y = 315
    for i, stage in enumerate(STAGES):
        x = 56 + i * 218
        if i < 5:
            arrow(d, (x + 190, y + 45), (x + 214, y + 45))
        selected = active == i
        rounded(d, (x, y, x + 190, y + 92), '#17382f' if selected else PANEL,
                ACCENT if selected else BORDER)
        centered(d, x + 95, y + 32, stage, 23, ACCENT if selected else MUTED, selected)
        if selected:
            d.rectangle((x + 20, y + 81, x + 170, y + 85), fill=ACCENT)
    rounded(d, (56, 455, 1344, 645))
    text(d, (86, 480), label, 19, ACCENT, mono=True)
    text(d, (86, 527), lines[0], 31, bold=True, mono=active is None and label == 'ONE SHORT REQUEST')
    text(d, (86, 584), lines[1], 23, MUTED)
    text(d, (58, 700), 'WORKFLOW ILLUSTRATION · EXAMPLE DATA', 18, MUTED, mono=True)
    text(d, (990, 700), 'Your issue. Your scope.', 22, ACCENT)
    return im


def build_gif():
    images = [frame(scene) for scene in SCENES]
    # Use a shared palette so unchanged elements remain stable between frames.
    palette = images[0].quantize(colors=128)
    frames = [im.quantize(palette=palette) for im in images]
    frames[0].save(ROOT / 'workflow-preview.gif', save_all=True, append_images=frames[1:],
                   duration=[scene[-1] for scene in SCENES], loop=0, optimize=True, disposal=1)
    images[1].save(ROOT / 'workflow-preview-poster.png')


def build_svg():
    pieces = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="650" viewBox="0 0 1400 650" role="img" aria-labelledby="title desc">
<title id="title">doforme: from issue to PR draft and owner-attested resolution</title>
<desc id="desc">Issue and confirmed requirements enter six sequential stages: Analyze, Plan, Fix, Test, Review, Draft PR. Scope approval precedes Fix. Publication, human review, CI, QA/UAT, merge, and issue closure are outside the runner. Optional Telegram notifications report new bugs and owner-attested resolution.</desc>
<rect width="1400" height="650" rx="20" fill="{BG}"/>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1L8 5L1 9" fill="none" stroke="{MUTED}" stroke-width="1.5"/></marker></defs>
<g font-family="DejaVu Sans, Arial, sans-serif">''']
    def t(x, y, value, size=24, color=TEXT, bold=False, anchor='start'):
        pieces.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{"700" if bold else "400"}" text-anchor="{anchor}">{escape(value)}</text>')
    def rect(x,y,w,h,stroke=BORDER,fill=PANEL):
        pieces.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" stroke="{stroke}" stroke-width="2" fill="{fill}"/>')
    def line(x1,y1,x2,y2):
        pieces.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{MUTED}" stroke-width="2" marker-end="url(#arrow)"/>')
    t(48,61,'The complete issue-to-resolution flow',42,bold=True)
    t(48,105,'A guided repair workflow, connected to your team’s delivery process.',24,MUTED)
    rect(48,145,1304,77)
    t(72,176,'GitHub issue or local ticket + confirmed requirements',25,bold=True)
    t(72,205,'You start the workflow. Optional Telegram reports new GitHub bug issues.',21,MUTED)
    pieces.append(f'<path d="M250 222V285H145V290" fill="none" stroke="{MUTED}" stroke-width="2" marker-end="url(#arrow)"/>')
    t(48,270,'INSIDE DOFORME',18,ACCENT,True)
    t(694,270,'Scope approval before Fix · gates check every handoff',21,MUTED)
    roles=['Investigate','Define scope','Repair','Verify AC','Check evidence','Prepare locally']
    for i, stage in enumerate(STAGES):
        x=48+i*222
        if i<5:line(x+194,345,x+216,345)
        rect(x,296,194,101,ACCENT if stage in ('Fix','Test') else BORDER)
        t(x+97,335,stage,25,TEXT,True,'middle')
        t(x+97,373,roles[i],20,MUTED,False,'middle')
    line(1255,402,1255,441)
    rect(48,454,1304,135)
    t(72,488,'YOUR TEAM’S DELIVERY PROCESS',18,ACCENT,True)
    t(72,530,'Publish with permission · human review · CI · QA/UAT · merge · close issue',25,bold=True)
    t(72,568,'Optional Telegram: resolved after merged-PR checks and owner evidence pass.',23,MUTED)
    t(48,626,'Runs can pause when requirements, permissions, or evidence are missing.',20,MUTED)
    pieces.append('</g></svg>')
    (ROOT/'workflow-overview.svg').write_text('\n'.join(pieces)+'\n')


if __name__ == '__main__':
    build_gif()
    build_svg()
    for name in ('workflow-preview.gif','workflow-preview-poster.png','workflow-overview.svg'):
        path=ROOT/name
        print(f'{name}: {path.stat().st_size:,} bytes')
