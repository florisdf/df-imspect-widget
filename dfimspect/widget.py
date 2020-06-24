from ipywidgets import HBox, VBox, BoundedIntText, Dropdown, Tab
from ipywidgets import HTML, Layout, Text, Button, FloatText, Play
import ipywidgets as widgets
from typing import List, Callable, Union
import pandas as pd
from .example import ImBoxWidget, CropBoxWidget, DetailsWidget
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging
from skvideo.io import FFmpegWriter
import numpy as np
from tqdm import tqdm_notebook as tqdm

DEFAULT_STYLE = {
    'stroke_width': 2,
    'stroke_color': '#ff0000',
    'fill_color': '#00000000',
    'hover_fill': '#00000088',
    'hover_stroke': '#0000ff',
    'active_fill': '#ffffff22',
    'active_stroke': '#00ff00',
    'font_family': 'arial',
    'font_size': 10
}


class ImBox(VBox):
    """Widget for inspecting images that contain bounding boxes."""
    def __init__(self, df: pd.DataFrame, box_col: str = 'box',
                 img_col: str = 'image',
                 text_cols: Union[str, List[str]] = None,
                 text_fmts: Union[Callable, List[Callable]] = None,
                 style_col: str = None):
        """
        :param pd.DataFrame df: `DataFrame` with images and boxes
        :param str box_col: column in the dataframe that contains boxes
        :param str img_col: column in the dataframe that contains image paths
        :param Union[str, List[str]] text_cols: (optional) the column(s) in the
        dataframe to use for creating the text that is shown on top of a box.
        When multiple columns are give, the text will be created by a
        comma-separated list of the contents of the given columns.
        :param Unions[Callable, List[Callable]] text_fmts: (optional) a
        callable, or list of callables, that takes the corresponding value from
        the `text_cols` column(s) as an input and returns the string to print
        for that value.
        :param str style_col: the column containing a dict of style attributes.
        Available attributes are:
            - `stroke_width`: the stroke width of a box (default 2)
            - `stroke_color`: the stroke color of a box (default 'red')
            - `fill_color`: the fill color of a box (default  '#00000000')
            - `hover_fill`: the fill color of a box when it is hovered on
              (default '#00000088')
            - `hover_stroke`: the stroke color of a box when it is hovered on
              (default 'blue')
            - `active_fill`: the fill color of a box when it is clicked on
              (default '#ffffff22')
            - `active_stroke`: the stroke color of a box when it is clicked on
              (default 'green')
            - `font_family`: the font family to use for box text (default
            'arial'). NOTE: exported text will always be Arial.
            - `font_size`: the font size in points (default 10)
        """
        if text_cols is None:
            text_cols = []
        if isinstance(text_cols, str):
            text_cols = [text_cols]
        if text_fmts is None:
            text_fmts = [None]*len(text_cols)
        if isinstance(text_fmts, Callable):
            text_fmts = [text_fmts]
        self.text_cols = text_cols
        self.text_fmts = text_fmts

        df2 = df.copy()

        def row2text(row):
            txts = row[text_cols]
            return ', '.join([fmt(txt) if fmt is
                              not None else
                              str(txt)
                              for txt, fmt in zip(txts, self.text_fmts)])

        if style_col is None:
            style_col = '_dfim_style'
            df2[style_col] = [DEFAULT_STYLE]*len(df2)
        else:
            df2[style_col] = df2[style_col].apply(lambda s:
                                                  {k: s[k] if k in s
                                                   else DEFAULT_STYLE[k]
                                                   for k in DEFAULT_STYLE})

        df2['box_text'] = df2.apply(lambda row: row2text(row), axis=1)
        df2['box_dict'] = df2.apply(lambda row: dict(index=row.name,
                                                     box=row[box_col],
                                                     text=row['box_text'],
                                                     style=row[style_col])
                                    if (box_col in row.index
                                        and row[box_col] is not None)
                                    else None,
                                    axis=1)

        self.df_img = df2.groupby(img_col).agg(list).reset_index()
        self.df = df
        self.img_col = img_col
        self.box_col = box_col

        # SELECTION widget
        self.idx_wgt = BoundedIntText(value=0,
                                      min=0,
                                      max=len(self.df_img) - 1,
                                      step=1,
                                      description='Choose index',
                                      disabled=False)
        self.drop_wgt = Dropdown(options=self.df_img[img_col],
                                 description='or image',
                                 value=None,
                                 disabled=False)
        self.drop_wgt.observe(self.drop_changed, names='value')
        self.idx_wgt.observe(self.idx_changed, names='value')
        self.imsel_wgt = VBox([self.idx_wgt, self.drop_wgt])
        self.imsel_wgt.layout = Layout(margin='auto')

        # IMAGE PANE
        self.img_title = HTML(placeholder='(Image path)')
        self.img_title.layout = Layout(margin='auto')
        self.imbox_wgt = ImBoxWidget()
        self.imbox_wgt.layout = Layout(margin='1em auto')
        self.imbox_wgt.observe(self.box_changed, names='active_box')
        self.imbox_wgt.observe(self.img_changed, names='img')

        # DETAILS PANE
        self.crop_wgt = CropBoxWidget()
        self.crop_wgt.layout = Layout(margin='0 1em')
        self.detail_wgt = DetailsWidget()
        self.detail_wgt.layout = Layout(margin='auto')
        self.detail_pane = HBox([self.crop_wgt, self.detail_wgt])
        self.detail_pane.layout = Layout(margin='1em auto')

        # PLAY widget
        self.play_btns = Play(interval=100,
                              value=0,
                              min=0,
                              max=len(self.df_img) - 1,
                              step=1,
                              description="Play",
                              disabled=False)
        self.play_slider = widgets.IntSlider(value=0,
                                             min=0,
                                             max=len(self.df_img) - 1,
                                             step=1)
        widgets.jslink((self.play_btns, 'value'), (self.idx_wgt, 'value'))
        widgets.jslink((self.play_btns, 'value'), (self.play_slider, 'value'))

        self.play_wgt = widgets.HBox([self.play_btns,
                                      self.play_slider])
        self.play_wgt.layout = Layout(margin='auto')

        # IMAGE EXPORT widget
        self.imexp_dest = Text(description='Output file',
                               value='output/output.png')
        self.imexp_btn = Button(description='Export')
        self.imexp_btn.on_click(self.export_img)
        self.imexp_wgt = HBox([self.imexp_dest, self.imexp_btn])

        # VIDEO EXPORT widget
        self.videxp_dest = Text(description='Output file',
                                value='output/output.mp4')
        self.videxp_start = BoundedIntText(value=0,
                                           min=0,
                                           max=len(self.df_img) - 1,
                                           step=1,
                                           description='From index',
                                           disabled=False)
        self.videxp_start.observe(self.vididx_changed, names='value')
        self.videxp_end = BoundedIntText(value=0,
                                         min=0,
                                         max=len(self.df_img) - 1,
                                         step=1,
                                         description='Until index',
                                         disabled=False)
        self.videxp_end.observe(self.vididx_changed, names='value')
        self.videxp_fps = FloatText(value=30, description='FPS')
        self.videxp_btn = Button(description='Export')
        self.videxp_btn.on_click(self.export_vid)

        self.videxp_wgt = VBox([HBox([self.videxp_start, self.videxp_end]),
                                HBox([self.videxp_dest, self.videxp_fps]),
                                self.videxp_btn])
        self.exp_wgt = Tab(children=[self.imexp_wgt, self.videxp_wgt])
        self.exp_wgt.set_title(0, 'Export image')
        self.exp_wgt.set_title(1, 'Export video')
        self.exp_wgt.layout = Layout(margin='0 1em')

        super().__init__([self.imsel_wgt,
                          VBox([self.img_title,
                                self.imbox_wgt,
                                self.play_wgt,
                                self.detail_pane]),
                          self.exp_wgt])
        self.idx_changed({'new': 0})

    def box_changed(self, change):
        if change['new'] is None:
            self.detail_wgt.data = {}
            self.crop_wgt.box = None
        else:
            new_idx = change['new']['index']
            self.detail_wgt.data = dict(self.df.loc[new_idx])
            self.crop_wgt.box = change['new']['box']

    def img_changed(self, change):
        new_img = change['new']
        self.detail_wgt.data = {}
        self.crop_wgt.img = new_img
        self.img_title.value = f'Image path: <a href="{new_img}">{new_img}</a>'
        self.imexp_dest.value = f'output/{Path(new_img).stem}.png'
        self.imexp_btn.button_style = ''
        self.imexp_btn.description = 'Export'
        self.imexp_btn.disabled = False

    def drop_changed(self, change):
        idx = self.df_img[self.df_img[self.img_col] == change['new']].index[0]
        self.idx = idx
        self.imbox_wgt.img = self.df_img.loc[idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[idx, 'box_dict']
        self.idx_wgt.value = idx

    def idx_changed(self, change):
        self.idx = change['new']
        self.imbox_wgt.img = self.df_img.loc[self.idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[self.idx, 'box_dict']
        self.drop_wgt.value = self.imbox_wgt.img

    def vididx_changed(self, change):
        start = self.videxp_start.value
        end = self.videxp_end.value
        self.videxp_dest.value = f'output/{start}_{end}.mp4'
        self.videxp_btn.button_style = ''
        self.videxp_btn.description = 'Export'
        self.videxp_btn.disabled = False

    def get_pilim_from_idx(self, idx):
        """Return the processed PIL image that belongs to an image index.
        """
        im = Image.open(self.df_img.loc[idx, self.img_col])
        draw = ImageDraw.Draw(im, mode='RGBA')

        box_dicts = self.df_img.loc[idx, 'box_dict']
        for bd in box_dicts:
            box = bd['box']
            draw.rectangle([(box.x_min, box.y_min),
                            (box.x_max, box.y_max)],
                           fill=bd['style']['fill_color'],
                           outline=bd['style']['stroke_color'],
                           width=bd['style']['stroke_width'])

            fontfile = str(Path(__file__).parent / 'etc/Arial.ttf')

            # size*4 to make it look more similar to example in widget
            fontsize = bd['style']['font_size']*4
            font = ImageFont.truetype(fontfile,
                                      size=fontsize)
            w, h = draw.textsize(bd['text'], font=font)
            draw.text((box.x_min, box.y_min - h),
                      text=bd['text'], fill=bd['style']['stroke_color'],
                      font=font)
        return im

    def export_img(self, button):
        self.imexp_btn.disabled = True
        self.imexp_btn.description = 'Exporting...'
        im = self.get_pilim_from_idx(self.idx)
        try:
            im.save(self.imexp_dest.value)
            self.imexp_btn.button_style = 'success'
            self.imexp_btn.description = 'Export Successful'
        except (IOError, KeyError) as e:
            self.imexp_btn.button_style = 'danger'
            self.imexp_btn.description = 'Export Failed'
            logging.exception('Export Failed')

    def export_vid(self, button):
        self.videxp_btn.disabled = True
        self.videxp_btn.description = 'Exporting...'
        fps = str(self.videxp_fps.value)
        writer = FFmpegWriter(self.videxp_dest.value,
                              inputdict={'-framerate': fps})

        for idx in tqdm(range(self.videxp_start.value,
                              self.videxp_end.value)):
            im = self.get_pilim_from_idx(idx)
            writer.writeFrame(np.array(im))

        try:
            writer.close()
            self.videxp_btn.button_style = 'success'
            self.videxp_btn.description = 'Export successful'
        except OSError as e:
            self.videxp_btn.button_style = 'danger'
            self.videxp_btn.description = 'Export failed'
            logging.exception('Export Failed')
