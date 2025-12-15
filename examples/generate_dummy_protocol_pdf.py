"""Generate a protocol with random values"""
import markdown
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from midomtoolbox.generators import ProtocolFactory
from midomtoolbox.render.markdown import render_protocol

protocol = ProtocolFactory.build()
protocol.sort_tags()  # Sort from specific to general

md_protocol = render_protocol(protocol)

html = markdown.markdown(md_protocol, extensions=["tables"])

font_config = FontConfiguration()
css = CSS(
    string="""
body{
    width:100%;
    font-size:1rem;
    line-height:1.8rem;
    font-weight:400;
    color:var(--color-text-tint-1, #575757);
    overflow-y:scroll;
    overflow-x:hidden;
    font-color: blue;
}
h1{
    font-size:2.5em;
    margin:.67em 0;
}

h2{
    font-size:2rem;
    margin:40px 0;
}
h3{
    margin:54px 0 24px;
    font-size:1.5rem;
}
table{
    border-collapse:collapse;
    border-spacing:0;
    border-collapse: collapse;

}
td,th{
    padding:0;
    font-size:0.6rem;
    line-height:0.8rem;
    border: 1px solid;
    padding: 0.5em;
}

""",
    font_config=font_config,
)

output_file = "/tmp/output.pdf"

HTML(string=html).write_pdf(output_file, stylesheets=[css])

print(f"Wrote '{output_file}'")
