"""DictaLM as judge between two Whisper drafts of the same segment.

Pure helpers (no MLX import) so they can be unit-tested; the model call is injected.
The primary (ivrit.ai) segment always keeps its timing; the judge only rewrites text.
"""
import re

JUDGE_MODEL = "alexandersdata/DictaLM-3.0-1.7B-Instruct-mlx-8Bit"

PROMPT = """לפניך שני תמלולים אוטומטיים של אותו קטע שמע בעברית.
תמלול א (מודל עברי, בדרך כלל מדויק יותר):
{a}
תמלול ב (מודל כללי, לבדיקה):
{b}
כתוב את הנוסח הנכון ביותר של הקטע. התחל מתמלול א, ותקן מילה רק כשהיא נראית שגויה ובתמלול ב יש קריאה הגיונית יותר.
אל תוסיף תוכן שלא מופיע באחד התמלולים, אל תסכם ואל תסביר.
החזר שורה אחת בלבד: הנוסח הסופי."""


def norm(text):
    """Compare-friendly form: no punctuation, single spaces."""
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def words_in(words, start, end):
    """Text of check-model words whose midpoint falls inside [start, end)."""
    return " ".join(w["word"].strip() for w in words
                    if start <= (w["start"] + w["end"]) / 2 < end).strip()


def accept(primary, verdict, alt=""):
    """Guard against judge drift: fall back to the primary when the verdict is unusable.

    The verdict may only pick between the drafts: every word must come from the primary
    or the alternate, and no primary word may be dropped (only replaced).
    """
    v = verdict.strip().splitlines()[0].strip() if verdict.strip() else ""
    v = re.sub(r"^[\"'״\s]*הנוסח הסופי\s*[:.\-–]?\s*", "", v).strip("\"'״ ")
    if not v or not re.search(r"[֐-׿]", v) and re.search(r"[֐-׿]", primary):
        return primary
    vw, pw, aw = (set(norm(x).split()) for x in (v, primary, alt))
    if alt and (vw - pw - aw or (pw & aw) - vw):
        return primary  # invented a word, or dropped one both drafts agree on
    if len(norm(v).split()) < len(norm(primary).split()):
        return primary  # may only replace words, never drop them
    if len(v) > 1.6 * len(primary) + 10 or len(v) < 0.5 * len(primary):
        return primary
    return v


def judge_segments(segs, check_words, ask, on_step=None):
    """Rewrite each segment's text with `ask(prompt) -> str` where the two drafts disagree.

    `on_step(done, total)` is called after each disputed segment is judged.
    """
    alts = [words_in(check_words, s["start"], s["end"]) for s in segs]
    disputed = [i for i, (s, a) in enumerate(zip(segs, alts)) if a and norm(a) != norm(s["text"])]
    out = [dict(s) for s in segs]
    if on_step:
        on_step(0, len(disputed))
    for n, i in enumerate(disputed, 1):
        out[i]["text"] = accept(segs[i]["text"], ask(PROMPT.format(a=segs[i]["text"], b=alts[i])), alts[i])
        if on_step:
            on_step(n, len(disputed))
    return out
