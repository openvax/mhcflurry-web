const autoprefixer = require('autoprefixer')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const path = require('path')

const loaders = {
  css: {
    loader: 'css-loader'
  },
  postcss: {
    loader: 'postcss-loader',
    options: {
      plugins: (loader) => [
        autoprefixer({
          browsers: ['last 2 versions']
        })
      ]
    }
  },
  sass: {
    loader: 'sass-loader',
    options: {
      indentedSyntax: true,
      includePaths: [path.resolve(__dirname, './src')]
    }
  },


}

const config = {
  entry: {
    app: ['./src/index']
  },

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      }, 

      {
        test: /\.css$/,
        use: ExtractTextPlugin.extract({
          fallback: 'style-loader',
          use: [loaders.css, loaders.postcss, loaders.sass]
        })
      },



      {
        test: /\.sass$/,
        use: ExtractTextPlugin.extract({
          fallback: 'style-loader',
          use: [loaders.css, loaders.postcss, loaders.sass]
        })
      }
    ]
  },

  output: {
    filename: '[name].js',
    path: path.join(__dirname, './static/build'),
    library: 'build',
    publicPath: '/static/build'
  },

  plugins: [new ExtractTextPlugin('[name].css')],

  resolve: {
    extensions: ['.js', '.sass', '.css'],
    modules: [path.join(__dirname, './src'), 'node_modules']
  }
}

module.exports = config
