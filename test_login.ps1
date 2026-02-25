$body = [System.Text.Encoding]::UTF8.GetBytes('{"email":"suryag.chinnathambi@gmail.com","password":"Surya@123"}')
$req = [System.Net.HttpWebRequest]::Create("http://localhost:8000/api/v1/auth/login")
$req.Method = "POST"
$req.ContentType = "application/json"
$req.ContentLength = $body.Length
$stream = $req.GetRequestStream()
$stream.Write($body, 0, $body.Length)
$stream.Close()
try {
    $resp = $req.GetResponse()
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    Write-Output "STATUS: $($resp.StatusCode)"
    Write-Output ($reader.ReadToEnd() | ConvertFrom-Json | ConvertTo-Json)
} catch [System.Net.WebException] {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
    Write-Output "HTTP $([int]$_.Exception.Response.StatusCode): $errBody"
}
