from traitlets import Unicode, List, Int, observe, Dict, Any
import ipywidgets as widgets
from flutil.shape import Box


def box2json(box):
    return ({'x': box.x_min, 'y': box.y_min,
             'width': box.width, 'height': box.height}
            if box is not None else None)


def json2box(json):
    return (Box.from_width_height(json['width'],
                                  json['height'],
                                  top_left=(json['x'], json['y']))
            if json is not None else None)


def imbox2json(imbox):
    return ({'index': imbox['index'],
             'box': box2json(imbox['box']),
             'style': imbox['style'] if 'style' in imbox else {}}
            if imbox is not None else None)


def json2imbox(json):
    return ({'index': json['index'],
             'box': json2box(json['box']),
             'style': json['style'] if 'style' in json else {}}
            if json is not None else None)


@widgets.register
class ImBoxWidget(widgets.DOMWidget):
    _view_name = Unicode('ImBoxView').tag(sync=True)
    _model_name = Unicode('ImBoxModel').tag(sync=True)
    _view_module = Unicode('df-imspect-widget').tag(sync=True)
    _model_module = Unicode('df-imspect-widget').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)

    img = Unicode().tag(sync=True)
    default_style = Dict({'stroke_width': 2,
                          'stroke_style': 'red',
                          'fill_style': '#00000000',
                          'hover_fill': '#00000088',
                          'hover_stroke': 'blue',
                          'active_fill': '#ffffff22',
                          'active_stroke': 'green'}).tag(sync=True)
    boxes = List().tag(sync=True,
                       to_json=lambda imboxes, widget:
                       [imbox2json(imbox) for imbox in imboxes])
    width = Int(500).tag(sync=True)
    height = Int(500).tag(sync=True)
    active_box = Any().tag(sync=True,
                           to_json=lambda imbox, widget:
                           imbox2json(imbox),
                           from_json=lambda json, widget:
                           json2imbox(json))

    @observe('img')
    def _observe_img(self, new):
        self.active_box = None
        self.boxes = []


@widgets.register
class CropBoxWidget(widgets.DOMWidget):
    _view_name = Unicode('CropBoxView').tag(sync=True)
    _model_name = Unicode('CropBoxModel').tag(sync=True)
    _view_module = Unicode('df-imspect-widget').tag(sync=True)
    _model_module = Unicode('df-imspect-widget').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)

    img = Unicode().tag(sync=True)
    box = Any().tag(sync=True,
                    to_json=lambda box, widget: box2json(box),
                    from_json=lambda json, widget: json2box(json))

    width = Int(150).tag(sync=True)
    height = Int(150).tag(sync=True)

    @observe('img')
    def _observe_img(self, new):
        self.box = None


@widgets.register
class DetailsWidget(widgets.DOMWidget):
    _view_name = Unicode('DetailsView').tag(sync=True)
    _model_name = Unicode('DetailsModel').tag(sync=True)
    _view_module = Unicode('df-imspect-widget').tag(sync=True)
    _model_module = Unicode('df-imspect-widget').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)

    attrs = List().tag(sync=True)
    data = Dict().tag(sync=True,
                      to_json=lambda data, widget: {k: str(v) for k, v in
                                                    data.items()})
