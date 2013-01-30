function get_rosinstall(distro, packages, gen_type)
{
  console.log("Building rosinstall for: " + distro + ", " + packages);
  Dajaxice.prerelease_website.rosinstall_gen.get_rosinstall_ajax(rosinstall_cb, 
		                                                 {'distro': distro,
							          'packages': packages,
								  'gen_type': gen_type});
}

function rosinstall_cb(data)
{
  console.log("Rosinstall generated");
  console.log(data);
  $("#status").html('Finished generating rosinstall file. If you are not redirected click <a href="/media/' + data.rosinstall_url + '">here</a>');
  window.location.replace("/media/" + data.rosinstall_url);
}
