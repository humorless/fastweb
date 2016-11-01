# How to setup 

  1. Install node.js 
  ```
  $ curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
  $ sudo apt-get update
  $ sudo apt-get install nodejs

  ```
  2. Install required package  
  ```
  $ git clone https://github.com/humorless/fastweb.git

  $ cd fastweb

  $ cd aggregate && npm install
  ```
  3. Fill suitable parameters in script `index.js`  
  ```
  var g = {
  -  id: '',
  -  pw: '',
  +  id: 'AAA',
  +  pw: 'BBB',
  }
  ```
  
  4. Change listening port if necessary in script `index.js`  
  ```
   app.listen(3005, function () {
     console.log('Example app listening on port 3005!');
  })

  ```
  5.  Invoke nodejs API server.   
  ```
  nodejs ./index.js
  ```
# How to use

  1. Get simple counter of certain platform. Simple counter is counter with only metric name and without tags. 
  Ex. platform is AAA
      metric is cpu.idle
  ``` 
  http://10.20.30.40:3005/api/platforms/AAA/metrics/cpu.idle  
  ``` 

  2. Get complex counter of certain platform. Complex counter is counter with tags.
  Ex. platform is AAA
      counter is disk.io.util, with tag as device=sda 
  ```
  http://10.20.30.40:3005/api/platforms/AAA/counters/disk.io.util
  ```
  
  3. Get complex counter of certain platform and with certain metric name and tag names.  
  ```
  http://10.20.30.40:3005/api/platforms/AAA/metrics/net.if.out.bits/tags/["iface=eth_all"] 
     
  ```
