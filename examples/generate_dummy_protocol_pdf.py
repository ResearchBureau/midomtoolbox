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

@page {
  margin: 5%;  /* weasy directive. 5% is UMCN recommended */
}

body{
    /* Reset all margins. I want maximum page usage*/
    margin: 0;
    padding: 0;
    box-sizing: border-box;

    font-family: Milo;
    #background-color: grey;
    width:100%;
    font-size:1rem;
    line-height:1.8rem;
    font-weight:400;
    #color:var(--color-text-tint-1, #575757);
    overflow-y:scroll;
    overflow-x:hidden;
    font-color: blue;
    padding: 0px;

}
h1{
    margin: 0;
    padding-top: 0.26em;
    border-top: 0.13em solid #00AFDC; /* Same thickness as dash */
    font-size:2.5em;
    width: 100%;
    color: #00AFDC;
    #margin:.67em 0;
}

h2{
    font-weight:200;
    font-size:2rem;
    width: 100%;
    color: #00AFDC;
    #margin:40px 0;
}
h3{
    #margin:54px 0 24px;
    width: 100%;
    font-size:1.5rem;
}
table{
    width: 98%;
    margin-left: 1%;
    #table-layout: fixed;
    border-collapse:collapse;
    border-spacing:0;
    border-collapse: collapse;
    border-bottom: 1pt solid #00AFDC;

}
th{
    background-color: #00AFDC;
    color:white;
}
td {
    color: black;
}
td,th{

    padding:0;
    font-size:0.6rem;
    line-height:0.8rem;
    border-left: 0.5pt solid white;
    padding: 1pt;
    padding-left: 1pt;
    padding-right: 1em;
}

""",
    font_config=font_config,
)

html_out_debug = "/home/sjoerd/Downloads/output.html"
output_file = "/tmp/output.pdf"

with open(html_out_debug, "w") as f:
    f.write(html)


HTML(string=html).write_pdf(output_file, stylesheets=[css])

print(f"Wrote '{output_file}'")
