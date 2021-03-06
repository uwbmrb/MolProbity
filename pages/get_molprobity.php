<?php

// We use a uniquely named wrapper class to avoid re-defining display(), etc.
class get_molprobity_delegate extends BasicDelegate {

#{{{ display - creates the UI for this page
############################################################################
/**
* Context is not used.
*/
function display($context)
{
    echo $this->pageHeader("Get MolProbity", "get_molprobity");
?>
Thanks for your interest in MolProbity!
MolProbity is <b>free and open source</b> software distributed under a BSD-style license.
MolProbity is developed and maintained by the <b>Richardson laboratory</b> at Duke University
(<a href='http://kinemage.biochem.duke.edu'>http://kinemage.biochem.duke.edu</a>).

<p>It is possible to download MolProbity and install it on a computer running <b>Linux or Mac OS X</b>.
This is the preferred mode of use for (1) organizations with confidential data (e.g. Big Pharma),
(2) institutions with very heavy usage (e.g. structural genomics centers),
and (3) groups that need automated or scripted MolProbity runs.</p>

<p>If you use MolProbity in the course of your research, please cite:
<br>
<div class='indent'>Vincent B. Chen, W. Bryan Arendall III, Jeffrey J. Headd, Daniel A. Keedy,
Robert M. Immormino, Gary J. Kapral, Laura W. Murray, Jane S. Richardson and David C. Richardson (2010)
MolProbity: all-atom structure validation for macromolecular crystallography.
Acta Crystallographica <u>D66</u>: 12-21.</div>
<br>
A complete list of appropriate citations can be
found <a href='help/about.html' target='_blank'>here</a>.</p>

<p><b>MolProbity is now on GitHub!</b>
The GitHub site is <a href='https://github.com/rlabduke/MolProbity' target="_blank">https://github.com/rlabduke/MolProbity</a>. You can look at the README there, or if you're already using git you can get a copy of MolProbity with:
<div align="center" style="font-size:20px">
git clone https://github.com/rlabduke/MolProbity.git --branch molprobity_4.2 --single-branch --depth 1
</dir>
<p>

<?php
$file = "jiffiloop.tgz";
if(file_exists($file) && filesize($file) > 0)
{
    echo "<p>For the optional jiffiloop functionality, download the following ";
    echo " file and untar it in the lib/ directory.";
    echo "<p><b>Download now: <a href='$file'>".basename($file)."</a></b>";
    echo ", ".formatFilesize(filesize($file));
    echo ", last updated ".date('j M Y', filemtime($file))."\n";
}
    echo $this->pageFooter();
}
#}}}########################################################################

}//end of class definition
?>
