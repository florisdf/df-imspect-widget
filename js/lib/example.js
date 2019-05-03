var widgets = require('@jupyter-widgets/base');
var _ = require('lodash');


// Custom Model. Custom widgets models must at least provide default values
// for model attributes, including
//
//  - `_view_name`
//  - `_view_module`
//  - `_view_module_version`
//
//  - `_model_name`
//  - `_model_module`
//  - `_model_module_version`
//
//  when different from the base class.

// When serialiazing the entire widget state for embedding, only values that
// differ from the defaults will be specified.
var ImBoxModel = widgets.DOMWidgetModel.extend({
  defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
    _model_name : 'ImBoxModel',
    _view_name : 'ImBoxView',
    _model_module : 'df-imspect-widget',
    _view_module : 'df-imspect-widget',
    _model_module_version : '0.1.0',
    _view_module_version : '0.1.0'
  })
});

var ImBoxView = widgets.DOMWidgetView.extend({
  render: function() {
    var div = document.createElement('div');

    this.bg = document.createElement('canvas');
    div.appendChild(this.bg);

    this.fg = document.createElement('canvas');
    this.fg.style.position = 'absolute';
    this.fg.style.left = '0px';
    this.fg.style.top = '0px';
    this.fg.onmousemove = this.onmousemove.bind(this);
    this.fg.onclick = this.onclick.bind(this);
    div.appendChild(this.fg);

    this.el.appendChild(div);

    this.im_scale = 1;
    this.draw_img();
    this.model.on('change:img', this.draw_img, this);
    this.model.on('change:boxes', this.draw_boxes, this);
    this.model.on('change:width', this.draw_img, this);
    this.model.on('change:height', this.draw_img, this);
    this.model.on('change:active_box', this.draw_boxes, this);
    this.model.on('change:default_style', this.draw_boxes, this);
  },

  draw_img: function() {
    var ctx = this.bg.getContext("2d");
    ctx.clearRect(0, 0, this.bg.width, this.bg.height);

    var img = new Image();
    img.src = this.model.get('img');

    var onImgLoad = function() {
      var w_scale = this.model.get('width') / img.width;
      var h_scale = this.model.get('height') / img.height;
      this.im_scale = Math.min(w_scale, h_scale, 1);

      let width = img.width*this.im_scale;
      let height = img.height*this.im_scale;

      this.bg.width = width;
      this.bg.height = height;
      this.fg.width = width;
      this.fg.height = height;

      ctx.drawImage(img, 0, 0, width, height);
      this.draw_boxes();
    }.bind(this);
    img.addEventListener('load' , onImgLoad);
  },

  draw_box: function(box) {
    var ctx = this.fg.getContext("2d");
    var im_scale = this.im_scale;

    var default_style = this.model.get('default_style');
    for (var prop in default_style) {
      if (default_style.hasOwnProperty(prop)
        && !box['style'].hasOwnProperty(prop)) {
        box['style'][prop] = default_style[prop];
      }
    }

    var active_box = this.model.get('active_box');
    var is_active = JSON.stringify(active_box) === JSON.stringify(box);
    if (is_active) {
      box = JSON.parse(JSON.stringify(box));
      box['style']['fill_style'] = box['style']['active_fill'];
      box['style']['stroke_style'] = box['style']['active_stroke'];
    }

    ctx.beginPath();
    ctx.lineWidth = box['style']['stroke_width'];
    ctx.strokeStyle = box['style']['stroke_style'];
    ctx.fillStyle = box['style']['fill_style'];
    ctx.rect(box['box']['x']*im_scale,
      box['box']['y']*im_scale,
      box['box']['width']*im_scale,
      box['box']['height']*im_scale);
    ctx.stroke();
    ctx.fill();
  },

  draw_dummy_box: function(box) {
    var im_scale = this.im_scale;
    var ctx = this.fg.getContext("2d");
    ctx.beginPath();
    ctx.lineWidth = 0;
    ctx.rect(box['box']['x']*im_scale,
      box['box']['y']*im_scale,
      box['box']['width']*im_scale,
      box['box']['height']*im_scale);
  },

  draw_boxes: function() {
    var ctx = this.fg.getContext("2d");
    ctx.clearRect(0, 0, this.fg.width, this.fg.height);

    var boxes = this.model.get('boxes');
    boxes.forEach(function(box) {
      if (box) {
        this.draw_box(box);
      }
    }.bind(this));
  },

  onmousemove: function(e) {
    // important: correct mouse position:
    var rect = this.fg.getBoundingClientRect(),
      x = e.clientX - rect.left,
      y = e.clientY - rect.top;

    var active_box = this.model.get('active_box');
    var ctx = this.fg.getContext("2d");
    ctx.clearRect(0, 0, this.fg.width, this.fg.height);
    this.model.get('boxes').forEach(function(box) {
      var is_active = JSON.stringify(active_box) === JSON.stringify(box);
      if (is_active) {
        this.draw_box(box);
        return;
      }
      this.draw_dummy_box(box);
      if (ctx.isPointInPath(x, y)) {
        var boxClone = JSON.parse(JSON.stringify(box));
        boxClone['style']['fill_style'] = boxClone['style']['hover_fill'];
        boxClone['style']['stroke_style'] = boxClone['style']['hover_stroke'];
        this.draw_box(boxClone);
      } else {
        this.draw_box(box);
      }
    }.bind(this));
  },

  onclick: function(e) {
    // important: correct mouse position:
    var rect = this.fg.getBoundingClientRect(),
      x = e.clientX - rect.left,
      y = e.clientY - rect.top;

    var active_box = JSON.parse(JSON.stringify(this.model.get('active_box')));
    var ctx = this.fg.getContext("2d");
    var any_clicked = this.model.get('boxes').some(function(box) {
      this.draw_dummy_box(box);
      var is_clicked = ctx.isPointInPath(x, y);
      var is_active = JSON.stringify(active_box) === JSON.stringify(box);
      if (is_clicked && !is_active) {
        active_box = box;
      }
      else if (is_clicked && is_active) {
        active_box = null;
      }
      return is_clicked;
    }.bind(this));
    if (! any_clicked) {
      active_box = null;
    }

    // Sync active boxes with Python
    this.model.set('active_box', active_box);
    this.touch();
  }
});


var CropBoxModel = widgets.DOMWidgetModel.extend({
  defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
    _model_name : 'CropBoxModel',
    _view_name : 'CropBoxView',
    _model_module : 'df-imspect-widget',
    _view_module : 'df-imspect-widget',
    _model_module_version : '0.1.0',
    _view_module_version : '0.1.0'
  })
});

var CropBoxView = widgets.DOMWidgetView.extend({
  render: function() {
    var div = document.createElement('div');

    this.canvas = document.createElement('canvas');
    div.appendChild(this.canvas);

    this.el.appendChild(div);

    this.redraw();
    this.model.on('change:img', this.redraw, this);
    this.model.on('change:box', this.redraw, this);
    this.model.on('change:width', this.redraw, this);
    this.model.on('change:height', this.redraw, this);
  },

  redraw: function() {
    var ctx = this.canvas.getContext("2d");
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    var box = this.model.get('box');
    if (!box) {
      return;
    }

    var w_scale = this.model.get('width') / box.width;
    var h_scale = this.model.get('height') / box.height;
    this.box_scale = Math.min(w_scale, h_scale);

    let width = box.width*this.box_scale;
    let height = box.height*this.box_scale;

    this.canvas.width = width;
    this.canvas.height = height;

    var img = new Image();
    img.src = this.model.get('img');

    var onImgLoad = function() {
      ctx.drawImage(img,
        box.x, box.y, // sx, sy
        box.width, box.height, // sWidth, sHeight
        0, 0, // dx, dy
        this.canvas.width, this.canvas.height // dWidth, dHeight
      );
    }.bind(this);
    img.addEventListener('load' , onImgLoad);
  },
});

var DetailsModel = widgets.DOMWidgetModel.extend({
  defaults: _.extend(widgets.DOMWidgetModel.prototype.defaults(), {
    _model_name : 'DetailsModel',
    _view_name : 'DetailsView',
    _model_module : 'df-imspect-widget',
    _view_module : 'df-imspect-widget',
    _model_module_version : '0.1.0',
    _view_module_version : '0.1.0'
  })
});

var DetailsView = widgets.DOMWidgetView.extend({
  render: function() {
    this.model.on('change:data', this.redraw, this);
    this.model.on('change:attrs', this.redraw, this);
  },
  redraw: function() {
    let tbl  = document.createElement('table');
    tbl.style = 'width: 100%;'
    let data = this.model.get('data');
    let attrs = this.model.get('attrs');

    if (attrs.length === 0) {
      attrs = Object.keys(data);
    }
    for (let attr of attrs.filter(k => data.hasOwnProperty(k))) {
      let tr = tbl.insertRow();
      let th = document.createElement('th');
      tr.appendChild(th);

      let td = tr.insertCell();
      th.appendChild(document.createTextNode(attr));
      td.appendChild(document.createTextNode(data[attr]));
    }

    const el = this.el;
    while (el.firstChild) { el.removeChild(el.firstChild); }
    el.appendChild(tbl);
  },
});

module.exports = {
  ImBoxModel: ImBoxModel,
  ImBoxView: ImBoxView,
  CropBoxModel: CropBoxModel,
  CropBoxView: CropBoxView,
  DetailsModel: DetailsModel,
  DetailsView: DetailsView
};
