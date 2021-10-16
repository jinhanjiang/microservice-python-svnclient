<?php
define('API_KEY', '10000');
define('API_TOKEN', '513b60e222800340e4d7a12f2454794e');

/**
 * 数组键值排序
 */
function tksort(&$array) {
  	ksort($array);
  	foreach(array_keys($array) as $k) {
    	if(gettype($array[$k])=="array") {
      		tksort($array[$k]);
      	}
    }
}

/**
 * 调用svn client微服务接口
 */
function svnClientCall($api, $params=array())
{
	// 加密前将参数值转为字符串
	$authInfo = array(
	    'key'=>strval(API_KEY),
	    'timestamp'=>strval(time()),
	    'version'=>'1.0',
	);
	ksort($authInfo); tksort($params);
	$authInfo['sign'] = hash('sha256', strval(stripslashes(json_encode($params)).'|'.json_encode($authInfo).'|'.API_TOKEN));
	$authInfo['auth-fields'] = implode(',', array_keys($authInfo));
	$authInfo['debug'] = true;

	$content = json_encode($params);
	$headers = array(
	    "Content-Type: application/json",
	    "X-Requested-With: XMLHttpRequest",
	    "User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
	);
	foreach($authInfo as $key=>$val) {
		$headers[] = "X-Api-{$key}: {$val}";
	}
	// 也可以通过file_put_contents提交请求
	// $rawHeader = implode("\r\n", $headers)."\r\n";
	// $ctx = stream_context_create(array(
	//     'http' => array(
	//         'method'  => 'POST',
	//         'header'  => $rawHeader,
	//         'content' => $content
	//     )
	// ));
	// $jsonResponse = file_get_contents("http://127.0.0.1:9005/{$api}", false, $ctx);
	// $jsonResponse = file_get_contents("http://192.168.2.18:9005/{$api}", false, $ctx);

	$url = "http://127.0.0.1:9005/{$api}";
	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $content);
	curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($ch, CURLOPT_TIMEOUT, 60);
	$jsonResponse = curl_exec($ch);
	return @json_decode($jsonResponse, true);
}

$data = svnClientCall('getAccountList', array('a'=>'123'));
print_r($data);die;