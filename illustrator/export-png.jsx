var path = "~/Adobe/_exports/" + "z" + app.activeDocument.name;

app.activeDocument.exportFile(new File("/Users/zachvp/Adobe/_exports/test_script_export"),
							  ExportType.PNG24,
							  new ExportOptionsPNG24());