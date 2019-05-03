var df-imspect-widget = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'df-imspect-widget',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'df-imspect-widget',
          version: df-imspect-widget.version,
          exports: df-imspect-widget
      });
  },
  autoStart: true
};

