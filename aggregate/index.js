var express = require('express');
var rp = require('request-promise');
var _ = require('lodash');

var app = express();

app.get('/', function (req, res) {
  res.send('Hello World!');
});

var g = {
  id: '',
  pw: '',
}

// req.params.platformID
// req.params.metricName
app.get('/api/platforms/:platformID/counters/:metricName', function (req, res) {
  var shared = {
    sig: '',
    hosts: []
  }

  var options = {
    method: 'POST',
    uri: 'http://owl.fastweb.com.cn/api/v1/auth/login',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    form: {'name': g.id, 'password': g.pw}
  }

  rp(options).then(function (body) {
      var json = JSON.parse(body)
      shared.sig = json.data.sig
      var hostgroup = [req.params.platformID]
      var options = {
        uri: 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: {'cName': g.id, 'cSig': json.data.sig, 'hostgroups': JSON.stringify(hostgroup)}
      }
      return rp(options)
    }).then(function (body) {
      var json = JSON.parse(body)
      var query = json.data.hosts.map(function (value) {
        return value.hostname
      })
      shared.hosts = query
      var options = {
        url: 'http://owl.fastweb.com.cn/api/v1/dashboard/endpointcounters',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: {
          'cName': g.id,
          'cSig': shared.sig,
          'metricQuery': req.params.metricName,
          'endpoints': JSON.stringify(query)
        }
      }
      return rp(options) 
    }).then(function (body) {
      var json = JSON.parse(body)
      //console.log(shared.hosts)
      var hosts_counters = shared.hosts.map(function (value) {
        return json.data.counters.map(function (counter){
          return [value, counter]
        })
      })
      //console.log(hosts_counters)
      var lists = [].concat.apply([], hosts_counters)
      //console.log(lists)
      var query = lists.map(function (value) {
        return {
            endpoint: value[0],
            counter: value[1]
        }
      })
      //console.log(query)
      var options = {
        url: 'http://query.owl.fastweb.com.cn/graph/last',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: JSON.stringify(query)
      }
      return rp(options) 
    }).then(function (body) {
      var json = JSON.parse(body)
      res.send(json)
    }) 
});
// req.params.platformID
// req.params.metricName
app.get('/api/platforms/:platformID/metrics/:metricName', function (req, res) {
  var options = {
    method: 'POST',
    uri: 'http://owl.fastweb.com.cn/api/v1/auth/login',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    form: {'name': g.id, 'password': g.pw}
  }

  rp(options).then(function (body) {
      var json = JSON.parse(body)
      var hostgroup = [req.params.platformID]
      var options = {
        uri: 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: {'cName': g.id, 'cSig': json.data.sig, 'hostgroups': JSON.stringify(hostgroup)}
      }
      return rp(options)
    }).then(function (body) {
      var json = JSON.parse(body)
      var query = json.data.hosts.map(function (value) {
        return {
            endpoint: value.hostname,
            counter: req.params.metricName
        }
      })
      var options = {
        url: 'http://query.owl.fastweb.com.cn/graph/last',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: JSON.stringify(query)
      }
      return rp(options) 
    }).then(function (body) {
      res.send(body)
    }) 
     
});

// req.params.platformID
// req.params.metricName
// req.params.tagsArray
app.get('/api/platforms/:platformID/metrics/:metricName/tags/:tagsArray', function (req, res) {
  var options = {
    method: 'POST',
    uri: 'http://owl.fastweb.com.cn/api/v1/auth/login',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    form: {'name': g.id, 'password': g.pw}
  }

  rp(options).then(function (body) {
      var json = JSON.parse(body)
      var hostgroup = [req.params.platformID]
      var options = {
        uri: 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: {'cName': g.id, 'cSig': json.data.sig, 'hostgroups': JSON.stringify(hostgroup)}
      }
      return rp(options)
    }).then(function (body) {
      var json = JSON.parse(body)
      //console.log(req.params.tagsArray)
      var tags = JSON.parse(req.params.tagsArray)
      //console.log(tags)
      var hosts_tags = json.data.hosts.map(function (value) {
        return tags.map(function (tag){
          return [value.hostname, tag]
        })
      })
      var lists = [].concat.apply([], hosts_tags)
      //console.log(lists)
      var query = lists.map(function (value) {
        var c_value = [req.params.metricName, value[1]].join('/')
        return {
            endpoint: value[0],
            counter: c_value
        }
      })
      //console.log(query)
      var options = {
        url: 'http://query.owl.fastweb.com.cn/graph/last',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        form: JSON.stringify(query)
      }
      return rp(options) 
    }).then(function (body) {
      res.send(body)
    }) 
     
});

app.listen(3005, function () {
  console.log('Example app listening on port 3005!');
})
