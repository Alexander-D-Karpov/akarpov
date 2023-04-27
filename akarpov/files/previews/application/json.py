from akarpov.files.models import File


def view(file: File):
    static = """
    <style>
    pre {outline: 1px solid #ccc; padding: 5px; margin: 5px; }
    .string { color: green; }
    .number { color: darkorange; }
    .boolean { color: blue; }
    .null { color: magenta; }
    .key { color: red; }
    </style>
    """
    if file.file_size < 200 * 1024:
        req = (
            f"""
    getJSON('{file.file.url}',
    """
            + """
    function(err, data) {
      if (err !== null) {
        console.log('Something went wrong: ' + err);
      } else {
        var str = JSON.stringify(data, undefined, 4);
        output(syntaxHighlight(str));
      }
    });
    """
        )
    else:
        req = """
        output("file is too large, download to view")
        """

    content = (
        """
    <div id="json" class="col-auto"></div>
    <script>
    function output(inp) {
        document.getElementById("json").appendChild(document.createElement('pre')).innerHTML = inp;
    }

    function syntaxHighlight(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(
/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\\s*:)?|\b(true|false|null)\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g,
        function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }
    var getJSON = function(url, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.responseType = 'json';
        xhr.onload = function() {
          var status = xhr.status;
          if (status === 200) {
            callback(null, xhr.response);
          } else {
            callback(status, xhr.response);
          }
        };
        xhr.send();
    };
    """
        + req
        + """
    </script>
    """
    )
    return static, content
