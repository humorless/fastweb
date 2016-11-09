#!/usr/bin/nodejs

var request = require('request');
var shell = require('shelljs/global');

// Set real parameters
var g = {
  id:'',
  pw:'',
  e: "docker-agent"
}

var localURL = {
  query: "http://10.20.30.40:9966",
  goAPIHost: "http://10.20.30.40:1234/api/v1"
}

//var URL = {
//  query: "http://query.owl.fastweb.com.cn",
//  goAPIHost: "http://owl.fastweb.com.cn/api/v1"
//}
var URL = localURL

var graphInfoHandler = function (error, response, body) {
  if (!error && response.statusCode == 200) {
    var json = JSON.parse(body)
    var filenames = json.map(function(t){ return t.filename })
    //console.log(filenames)
    //console.log(json)

    var hostDIR = '.'
    filenames.map( function(fname) {
      var sourceFile = 'graph:' + fname
      var cmd_str = ' docker cp ' + sourceFile + ' '+ hostDIR
      //console.log(cmd_str)
      // Run external tool synchronously
      if (exec(cmd_str).code !== 0) {
        echo('Error: docker cp failed');
        exit(1);
      }
      return null
    })
  } else {
    console.log(error)
  }
}

// query the API to get the counters from certain endpoints 
var endpointCountersHandler = function (error, response, body) {
  if (!error && response.statusCode == 200) {
    var json = JSON.parse(body)
    var e = g.e
    var queryData = json.data.counters.map(function(item){
      return {"endpoint": e, "counter": item}
    })
    var optionGraph = {
        url: URL.query + '/graph/info',
        method: 'POST',
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(queryData)
    }
    request(optionGraph, graphInfoHandler) 
  } else {
    console.log(error)
  }
}

// Start the request
var loginHandler = function (error, response, body) {
    if (!error && response.statusCode == 200) {
        // Print out the response body
        var json = JSON.parse(body)
        var e = JSON.stringify([g.e])
        var m = '.+'
        var options = {
            url: URL.goAPIHost + '/dashboard/endpointcounters',
            method: 'POST',
            headers: {"Content-Type": "application/x-www-form-urlencoded"},
            form: {'cName': g.id, 'cSig': json.data.sig, 'endpoints': e, 'metricQuery':m}
        }
        request(options, endpointCountersHandler)
    } else {
        console.log(error)
    }
}

// Configure the request
var options = {
    url: URL.goAPIHost + '/auth/login',
    method: 'POST',
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    form: {'name': g.id, 'password': g.pw}
}

request(options, loginHandler)
