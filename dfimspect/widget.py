from ipywidgets import HBox, VBox, BoundedIntText, Dropdown
import pandas as pd
from .example import ImBoxWidget, CropBoxWidget, DetailsWidget


class ImBox(VBox):
    """Widget for inspecting images that contain bounding boxes."""
    def __init__(self, df: pd.DataFrame, box_col='box', img_col='image',
                 style_col=None):
        df2 = df.copy()
        df2['box_dict'] = df.apply(lambda row: dict(index=row.name,
                                                    box=row[box_col],
                                                    style=row[style_col]
                                                    if style_col is not None
                                                    else {}),
                                   axis=1)
        self.df_img = df2.groupby(img_col).agg(list).reset_index()

        self.imbox_wgt = ImBoxWidget()
        self.crop_wgt = CropBoxWidget()
        self.detail_wgt = DetailsWidget()

        self.idx_wgt = BoundedIntText(value=None,
                                      min=0,
                                      max=len(self.df_img),
                                      step=1,
                                      description='Index',
                                      disabled=False)

        self.drop_wgt = Dropdown(options=self.df_img[img_col],
                                 description='Image',
                                 value=None,
                                 disabled=False)
        self.df = df
        self.img_col = img_col
        self.box_col = box_col

        self.imbox_wgt.observe(self.box_changed, names='active_box')
        self.imbox_wgt.observe(self.img_changed, names='img')
        self.drop_wgt.observe(self.drop_changed, names='value')
        self.idx_wgt.observe(self.idx_changed, names='value')
        super().__init__([self.drop_wgt,
                          self.idx_wgt,
                          HBox([self.imbox_wgt,
                                VBox([self.crop_wgt,
                                      self.detail_wgt])])])

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

    def drop_changed(self, change):
        idx = self.df_img[self.df_img[self.img_col] == change['new']].index[0]
        self.imbox_wgt.img = self.df_img.loc[idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[idx, 'box_dict']
        self.idx_wgt.value = idx

    def idx_changed(self, change):
        idx = change['new']
        self.imbox_wgt.img = self.df_img.loc[idx, self.img_col]
        self.imbox_wgt.boxes = self.df_img.loc[idx, 'box_dict']
        self.drop_wgt.value = self.imbox_wgt.img
