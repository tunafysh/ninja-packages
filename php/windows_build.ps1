Set-PSResourceRepository -Name PSGallery -Trusted -Confirm:$false
Install-PSResource -Name BuildPhp -Confirm:$false
$arch = if ([System.Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
$phpVersion = "8.5.4"
Invoke-PhpBuild -PhpVersion $phpVersion -Ts nts -Arch $arch