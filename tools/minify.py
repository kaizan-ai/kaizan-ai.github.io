"""Dependency-free CSS/JS minifier used by tools/build.py.

Deliberately conservative: it removes comments and redundant whitespace but never
renames, reorders or rewrites code, so the sources in assets/css and assets/js stay
the single readable source of truth and the output is behaviourally identical.

JS keeps line breaks (only indentation and blank lines go), so automatic semicolon
insertion behaves exactly as in the source.
"""
import re

_REGEX_PREV = set('(,=:[!&|?{};+-*%<>~^')
_REGEX_KEYWORDS = ('return', 'typeof', 'case', 'delete', 'void', 'throw', 'in', 'of', 'else', 'do', 'new')


def minify_css(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in '"\'':
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == '\\' else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith('/*', i):
            j = src.find('*/', i + 2)
            i = n if j < 0 else j + 2
        elif c == '(' and src[max(0, i - 3):i].lower() == 'url' and src[i + 1:i + 2] not in '"\'':
            j = src.index(')', i)          # unquoted url(...): copy verbatim
            out.append(src[i:j + 1])
            i = j + 1
        else:
            out.append(c)
            i += 1
    css = ''.join(out)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r' ?([{};,]) ?', r'\1', css)
    css = re.sub(r': ', ':', css)
    css = css.replace(';}', '}')
    return css.strip() + '\n'


def minify_js(src: str) -> str:
    out, i, n = [], 0, len(src)
    last = ''                      # last significant (non-space) char emitted
    last_word = ''

    def emit(s):
        nonlocal last, last_word
        out.append(s)
        stripped = s.rstrip()
        if stripped:
            last = stripped[-1]
            m = re.search(r'[A-Za-z_$][\w$]*$', stripped)
            last_word = m.group(0) if m else ''

    while i < n:
        c = src[i]
        if c in '"\'':
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == '\\' else 1
            emit(src[i:j + 1])
            i = j + 1
        elif c == '`':
            j, depth = i + 1, 0
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src.startswith('${', j):
                    depth += 1
                    j += 2
                    continue
                if src[j] == '}' and depth:
                    depth -= 1
                elif src[j] == '`' and not depth:
                    break
                j += 1
            emit(src[i:j + 1])
            i = j + 1
        elif src.startswith('//', i):
            j = src.find('\n', i)
            i = n if j < 0 else j
        elif src.startswith('/*', i):
            j = src.find('*/', i + 2)
            i = n if j < 0 else j + 2
        elif c == '/' and (last == '' or last in _REGEX_PREV or last_word in _REGEX_KEYWORDS):
            j, in_class = i + 1, False
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src[j] == '[':
                    in_class = True
                elif src[j] == ']':
                    in_class = False
                elif src[j] == '/' and not in_class:
                    break
                j += 1
            j += 1
            while j < n and src[j].isalpha():
                j += 1
            emit(src[i:j])
            i = j
        else:
            emit(c)
            i += 1
    lines = [ln.strip() for ln in ''.join(out).split('\n')]
    return '\n'.join(ln for ln in lines if ln) + '\n'
