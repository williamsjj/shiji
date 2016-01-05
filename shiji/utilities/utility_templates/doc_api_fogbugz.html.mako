# -*- coding: utf-8-*-
<!--##################################################################
 #FILENAME: ./doc_api_fogbugz.html.mako
 #PROJECT: 
 #DESCRIPTION: API Documentiation Template (FogBugz Wiki Format)
 #
 #
 ####################################################################
-->
<h3>
	<img alt="Table of Contents" plugin_content="" plugin_data="{'fIncludeH1':'True', 'fIncludeH6':'True', 'fIncludeH2':'True', 'fIncludeH3':'True', 'Version':'0', 'fIncludeH4':'True', 'fIncludeH5':'True'}" plugin_type="toc" src="default.asp?pg=pgTextToImage&amp;sText=Table%20of%20Contents" style="border: 1px solid #6BA1AF; margin-left: 2px; margin-right: 2px; padding: 1px; background-color: #E9F0F6;" title="Table of Contents" /></h3>
% for version in sorted(versions.keys(), reverse=True):
<h3>version ${version}</h3>
<h4>calls</h4>
<p>&nbsp;</p>
	% for call in sorted(versions[version]["calls"].keys()):
<table class="Basic" style="width:90%;">
	<tbody>
		<tr>
			<th colspan="2">${call | h}</th>
		</tr>
		% for method in versions[version]["calls"][call]:
		<tr>
			<td>${method}</td>
			<td><div>${versions[version]["calls"][call][method].replace("\\n", "<br/>")}</div>
			</td>
		</tr>
		% endfor
	</tbody>
</table>
	% endfor
<h4>error codes</h4>
	% for code in sorted(versions[version]["error_codes"].keys(), lambda x,y: versions[version]["error_codes"][x]["error_code"]-versions[version]["error_codes"][y]["error_code"]):
    <table class="Basic" style="width:90%;">
    	<tbody>
    		<tr>
    			<th colspan="2">${code | h}</th>
    		</tr>
    		<tr>
    		    <td style="width:10%">${versions[version]["error_codes"][code]["error_code"]}</td>
    		    <td style="width:90%">${versions[version]["error_codes"][code]["exception_text"]}</td>
    	</tbody>
    </table>
	% endfor
% endfor
