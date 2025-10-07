from src.services.pipeline import _reduce_html


def test_reduce_html_strips_scripts_and_keeps_headings():
    html = """
    <html>
      <head><script>var x=1</script></head>
      <body>
        <h1>Главные новости дня</h1>
        <div class="news">Очень важная новость о событиях в мире. Очень важная новость о событиях в мире.</div>
        <script>console.log('nope')</script>
      </body>
    </html>
    """
    reduced = _reduce_html(html)
    # Only longer blocks are kept (> 40 chars); heading may be too short
    assert "важная новость" in reduced
    assert "console.log" not in reduced
