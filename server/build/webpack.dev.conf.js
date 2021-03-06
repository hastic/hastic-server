const base = require('./webpack.base.conf');

const webpack = require('webpack');

base.mode = 'development';
base.watch = true;
base.output.filename = "server-dev.js";

// https://webpack.js.org/configuration/devtool/
base.devtool = 'inline-source-map';

base.externals = base.externals ? base.externals : [];
base.externals.push(
  function(context, request, callback) {
    if(request[0] == '.') {
      callback();
    } else {
      callback(null, "require('" + request + "')");
    }
  }
);

base.plugins = base.plugins ? base.plugins : [];
base.plugins.push(new webpack.DefinePlugin({
  'process.env.NODE_ENV': JSON.stringify('development')
}));

module.exports = base;
