import zipfile
from collections import defaultdict

from akarpov.files.models import File

FILE_MARKER = "<files>"


def attach(branch, trunk):
    """
    Insert a branch of directories on its trunk.
    """
    parts = branch.split("/", 1)
    if len(parts) == 1:  # branch is a file
        trunk[FILE_MARKER].append(parts[0])
    else:
        node, others = parts
        if node not in trunk:
            trunk[node] = defaultdict(dict, ((FILE_MARKER, []),))
        attach(others, trunk[node])


def to_li(d, indent=0):
    """
    Convert tree like structure to html ul li
    """
    res = ""
    for key, value in d.items():
        if key != FILE_MARKER:
            if indent >= 2 or str(key).startswith("."):
                in_res = (
                    """
                <li data-jstree='{ "opened" : false }'>
                """
                    + str(key)
                    + "<ul>"
                )
            else:
                in_res = (
                    """
                <li data-jstree='{ "opened" : true }'>
                """
                    + str(key)
                    + "<ul>"
                )
            r_res = ""
            c_res = """</ul></li>"""
            if isinstance(value, dict):
                r_res += to_li(value, indent + 1)
            else:
                if value is not str and isinstance(value, list):
                    for v in value:
                        if v:
                            r_res += (
                                """<li data-jstree='{ "opened" : true, "type" : "file" }'>"""
                                + str(v)
                                + "</li>"
                            )
                else:
                    if value:
                        r_res += (
                            """<li data-jstree='{ "opened" : true, "type" : "file" }'>"""
                            + str(value)
                            + "</li>"
                        )
            res += in_res + r_res + c_res
        else:
            if value is not str and isinstance(value, list):
                for v in value:
                    if v:
                        res += (
                            """<li data-jstree='{ "opened" : true, "type" : "file" }'>"""
                            + str(v)
                            + "</li>"
                        )
            else:
                if value:
                    res += (
                        """<li data-jstree='{ "opened" : true, "type" : "file" }'>"""
                        + str(value)
                        + "</li>"
                    )
    return res


def view(file: File) -> (str, str):
    zip = zipfile.ZipFile(file.file.path)

    root = defaultdict(dict, ((FILE_MARKER, []),))
    for line in zip.namelist():
        attach(line, root)
    r = str(to_li(root))

    static = """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.2.1/themes/default/style.min.css" />
    """
    content = (
        """
    <div class="col-auto">
    <div id="jstree_demo_div">
        <ul data-jstree='{ "opened" : true }>"""
        + f"""
            {file.file.path.split("/")[-1]}
        """
        + """
        <li data-jstree='{ "opened" : true }>
        """
        + f"""
            {r}
        </li>
    </ul>
    </div>
     </div>
     """
        + """
    <script src="/static/js/jquery.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.2.1/jstree.min.js"></script>
    <script>
    $(function () {


$('#jstree_demo_div').jstree({
    "core" : {
        "themes" : {
            "responsive": false
        }
    },
    "types" : {
        "default" : {
            "icon" : "bi bi-folder"
        },
        "file" : {
            "icon" : "bi bi-file-earmark-fill"
        }
    },
    "plugins": ["types"]
});


     });
    </script>
    """
    )
    return static, content
