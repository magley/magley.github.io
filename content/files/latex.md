---
title: LaTeX templates
date: 2025-04-07
math: true
---

My university doesn't provide $\LaTeX$ templates for papers, articles, theses etc.
Everything is in Microsoft Word. 
I'd rather shoot myself than write a large document in Word, let alone one that requires
math typesetting and code snippets.

This is a $\LaTeX$ class I made that's suitable for a graduate thesis.
It's more or less just a bunch of packages for code listings, math, support for Serbian cyrillic script, quality of life improvements etc.
There's also a custom title page macro I painstakingly designed by eyeballing against the "official" Word template.

You can download the thesis `.cls` file [here](https://raw.githubusercontent.com/magley/unsthesis/refs/heads/master/unsthesis.cls),
or alternatively check out the [github repo](https://github.com/magley/unsthesis) which includes an example.

Should you need a page with a complex format, it's better to write it in a WYSIWYG editor and import the PDF output using the [pdfpages](https://www.ctan.org/pkg/pdfpages) package:

```latex
\includepdf{thefile.pdf}
```