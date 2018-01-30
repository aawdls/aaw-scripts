
page_head="""<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="initial-scale=1.0, maximum-scale=2.0">
	<title>Parallel log file view</title>

	<style type="text/css">
	td, th{
	    font-family: monospace
	}
	</style>
	
</head>
"""
page_end="""</body>
</html>
"""
body_start="""<body class="dt-example">
"""
table_head="""<table id="example" class="display" cellspacing="0" width="100%">
  <thead>
    <tr>
      <th>{file1}</th>
      <th>{file2}</th>
    </tr>
  </thead>

  <tfoot>
    <tr>
      <th>{file1}</th>
      <th>{file2}</th>
    </tr>
  </tfoot>

  <tbody>
"""
table_bottom="""</table>
"""

one_row = """
    <tr>
        <td>{col1}</td>
        <td>{col2}</td>
    </tr>
"""
iframe = """
    <iframe src="00.html" name="hour_page" width="100%" height="700"></iframe>
"""