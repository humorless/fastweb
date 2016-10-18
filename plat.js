#!/usr/bin/nodejs

var request = require('request');

// Set real parameters
var g = {
  id:'',
  pw:'',
  hostgroups: '["c01.i01"]'
}


// Set the headers
var headers = {
    'User-Agent':       'Super Agent/0.0.1',
    'Content-Type':     'application/x-www-form-urlencoded'
}

// Configure the request
var options = {
    url: 'http://owl.fastweb.com.cn/api/v1/auth/login',
    method: 'POST',
    headers: headers,
    form: {'name': g.id, 'password': g.pw}
}

var queryHandler = function(error, response, body) {
  if (!error && response.statusCode == 200) {
    var json = JSON.parse(body)
    console.log(body)
  } else {
    console.log(error)
  }
}

var hostgroupHandler = function (error, response, body) {
  if (!error && response.statusCode == 200) {
    var json = JSON.parse(body)
    var query = json.data.hosts.map(function (value) {
      var ret = {
          counter: "cpu.idle",
          endpoint: value.hostname
      }
      return ret
    })
    var options = {
        url: 'http://query.owl.fastweb.com.cn/graph/last',
        method: 'POST',
        headers: headers,
        form: JSON.stringify(query)
    }

    request(options, queryHandler)
  } else {
    console.log(error)
  }
}
// Start the request
var loginHandler = function (error, response, body) {
    if (!error && response.statusCode == 200) {
        // Print out the response body
        var json = JSON.parse(body)
        var options = {
            url: 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
            method: 'POST',
            headers: headers,
            form: {'cName': g.id, 'cSig': json.data.sig, 'hostgroups': g.hostgroups}
        }

        request(options, hostgroupHandler)
    } else {
        console.log(error)
    }
}

request(options, loginHandler)
