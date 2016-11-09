#!/usr/bin/nodejs

var request = require('request');
var shell = require('shelljs/global');
var path = require('path');
// Set real parameters
var g = {
  id:'',
  pw:'',
  e: "docker-agent",   // endpoint name
  localDIR: './RRD',
  outDIR: './RRDout',
  dockerName: 'graph',
  timestampMax: 1414782122
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

    filenames.map( function(fname) {
      var sourceFile = g.dockerName + ':' + fname
      var cmd_str = ' docker cp ' + sourceFile + ' '+ g.localDIR
      //console.log(cmd_str)
      // Run external tool synchronously
      if (exec(cmd_str).code !== 0) {
        echo('Error: docker cp failed');
        exit(1);
      }
      // rrdtool dump in.rrd  | ./remove_samples_newer_than.py 1414782122 | rrdtool restore - out.rrd
      var in_rrd_file = g.localDIR + '/' + path.basename(fname)
      var out_rrd_file = g.outDIR + '/' + path.basename(fname)
      var timestampMax = g.timestampMax
      var cmd_rrd_remove = 'rrdtool dump ' + in_rrd_file + ' | ' + './remove_samples_newer_than.py ' + timestampMax + ' | rrdtool restore - ' + out_rrd_file

      //console.log(cmd_rrd_remove)

      if (exec(cmd_rrd_remove).code !== 0) {
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
