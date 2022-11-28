import os
import rioxarray 
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets
from datetime import datetime

class trend(object):
    def __init__(self, nc_file, shp):
        """Initializes the GRACE mascon trend object.
        
        Arguments:
            - csr_file: Path to the GRACE netcdf file.
            - shp: the Shape that will be used to clip
                the GRACE data as a geopandas data frame.
        """
        self.csr_url = \
        'http://download.csr.utexas.edu/outgoing/grace/RL06_mascons/CSR_GRACE_GRACE-FO_RL06_Mascons_all-corrections_v02.nc'
        self.nc_file = nc_file
        if not os.path.isfile(self.nc_file):
            print("Downloading the netcdf data from")
            print(f"{self.csr_url}")
            self.update_data()
        self.xr = self._load_data()
        self.shp = shp
        self.xrc = self._clip_data()
        self.ts = self._reduce_ts()


    def _load_data(self):
        """Loads the netcdf data as an xarray.Dataset
        """
        csr_data = xr.open_dataset(self.nc_file)
        # Technical note: the netcdf above breaks a CF convention
        # by capitalizing the units attribute (i.e. should be "units" and not "Units"). 
        # Here we assign the correct one (not capitalized) so that xarray
        # can decode the time correctly:
        csr_data.time.attrs.update(units=csr_data.time.Units)
        csr_data = (xr.decode_cf(csr_data)
        .rename({'lon':'x', 'lat':'y'})
        .drop_vars("time_bounds")
        .rio.write_crs("epsg:4326")
        )
        return csr_data


    def _clip_data(self):
        """Clips the dataset to the geometry in the shp
        1. First clips to the bounding box
        2. Then clips to the shape
        """
        csr_data_box = self.xr.rio.clip_box(**self.shp.bounds.iloc[0].to_dict())  
        clipped = csr_data_box.rio.clip(self.shp.geometry.values, self.shp.crs).drop("WGS84") 
        return clipped


    def update_data(self):
        """Re-downloads the CSR netcdf data
        
        Optional! only use if the existing nc file is out of date, or 
        if the file doesn't exist yet. 
        Takes about 2 minutes, depending on the download speed.
        The size is about 800MB. 
        """
        csr_file = self.nc_file 
        import requests
        r = requests.get(self.csr_url)
        grace_data = r.content
        with open(csr_file, 'wb') as f:
            f.write(grace_data)


    def _reduce_ts(self):
        """Reduce the data to a time series (returns a pandas DataFrame)
        Spatial mean at each time to get time series
        """
        ts_saq = (self.xrc
        .lwe_thickness.mean(dim=["x","y"]) 
        .to_dataframe()                    
        .rename_axis("date")
        .rename(columns={"lwe_thickness":"twsa"})
        )
        ts_saq.twsa = ts_saq.twsa*10 # cm->mm
        return ts_saq

    def display_ts(self):
        """Displays the widgets to visualize the time series
        """
        self._create_widgets()

    @staticmethod
    def _calc_trend_in_mm_year(df, y="twsa"):
        """Calculate a linear trend in mm/year

        The dataframe df has the dates as index. 

        Returns the trend and the predicted y values
        using the linear model. 
        """
        import pandas as pd
        import sklearn.linear_model
        model = sklearn.linear_model.LinearRegression()
        model.fit(df.index.values.reshape(-1, 1), df[y])
        trend = model.coef_*1e9*3600*24*365  # in mm/year
        # Note that the .astype(float) makes the date
        # a numeric value in nanoseconds! 
        y_pred = model.predict(df.index.values.astype(float).reshape(-1,1))
        y_pred = pd.Series(y_pred, index=df.index)
        return trend, y_pred

    def make_figure(self,Start,End):
        """Makes the figure using Start and End parameters

        The figure shows the TWSA time series
        and a shaded period (defined by Start/End) where we calculate
        a linear trend and display its value in mm.yr⁻¹
        """
        #hfont = {'fontname':'Arial'}
        height=2.75
        AR=3.5
        width = height*AR

        data = self.ts.copy()
        trend, y_pred = self._calc_trend_in_mm_year(data.query("date>=@Start and date<=@End"))   
        self.trend = trend
        data = data.assign(linear_twsa=y_pred)

        # Preview time series using seaborn
        og_grace_query="date<='2017-05-23'"
        gracefo_query="date>='2018-06-01'"

        fig =  plt.figure(figsize=(width, height))  
        ax = fig.add_subplot(1, 1, 1)
        sns.lineplot(data=data.query(og_grace_query), x="date", y="twsa", color="#484848", ax=ax)
        sns.lineplot(data=data.query(gracefo_query), x="date", y="twsa", ax = ax, color="#484848")
        # Linear trend:
        sns.lineplot(data=data.query("date>@Start"), x="date", y="linear_twsa", ax = ax, color="black")

        ax.set_xlabel("")
        ax.set_ylabel("Total Water Storage A.(mm)", fontsize=14)#, **hfont)
        ax.set_title("Estimated depletion represented as Total Water Storage Anomaly (TWSA)", fontsize=14)#, **hfont)

        # "Saq aquifer" annotation:
        annotate_kws = {"size": 16, "xytext": (0,0), "textcoords": "offset points", "fontweight": "bold"}
        ax.annotate("Saq Aquifer", (pd.to_datetime("2009-01-01"), -150), **annotate_kws)

        # "- X mm.yr^-1" annotation:
        trend_annot = "{:.2f} mm.yr⁻¹".format(trend[0])
        annotate_kws = {"size": 16, "xytext": (0,0), "textcoords": "offset points"}
        ax.annotate(trend_annot, (pd.to_datetime("2009-01-01"), 30), **annotate_kws)

        plt.setp(ax.get_yticklabels(), fontsize=14)#, **hfont)
        plt.setp(ax.get_xticklabels(), fontsize=14)#), **hfont)
        plt.axvspan(Start, End, facecolor='#D3D3D3')
        plt.rcParams['svg.fonttype'] = 'none' # so that the
        # fonts in the exported svg can be edited e.g. in powerpoint.  
        #fig.canvas.draw()
        self.fig = fig 

    def to_svg(self, file_name, **kwargs):
        self.fig.savefig(file_name, **kwargs) 
        #dpi = 600, bbox_inches = 'tight', transparent = True)

    def to_png(self, file_name, **kwargs):
        self.fig.savefig(file_name, **kwargs) 

    def _create_widgets(self):
        default_start_date = datetime(2007, 1, 1)
        default_end_date = datetime(2022, 8, 15)
        start_date = datetime(2002, 1, 1)
        end_date = datetime(2022, 12, 31)
        dates = pd.date_range(start_date, end_date, freq='D')
        options = {date.strftime(' %d %b %Y '): date for date in dates}
        pick_start = ipywidgets.widgets.DatePicker(
            description='',
            disabled=False,
            value = default_start_date
        )
        pick_end = ipywidgets.widgets.DatePicker(
            description='',
            disabled=False,
            value=default_end_date
        )
        selection_range_slider = ipywidgets.widgets.SelectionRangeSlider(
            options=options,
            index=(0, len(options) - 1),
            continuous_update=False,
            description='Trend period',
            orientation='horizontal',
            layout=ipywidgets.widgets.Layout(width='100%', padding='35px')
        )
        def update_pick(*args):
            pick_start.value = selection_range_slider.value[0]
            pick_end.value = selection_range_slider.value[1]

        def update_slider(*args):
            selection_range_slider.value =  (pick_start.value, pick_end.value)
        
        selection_range_slider.observe(update_pick, 'value')
        pick_start.observe(update_slider, 'value')
        pick_end.observe(update_slider, 'value')
        center_layout = ipywidgets.widgets.Layout(display='flex',
                                               align_items='center',
                                               width='100%')
        control = ipywidgets.widgets.HBox(children=[
            #pick_start, 
            selection_range_slider, 
            #pick_end
            ], layout=center_layout)
       

        update_slider('value')
        display(control)
        ipywidgets.interact(self.make_figure, Start=pick_start, End=pick_end)

