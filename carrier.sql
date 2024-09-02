CREATE schema greensight_carrier;
CREATE TABLE [greensight_carrier].[pepsi_shipments](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[shipment_identifier] [nvarchar](50) NULL,
	[pickup_date_time] [datetime2](7) NULL,
	[delivery_date_time] [datetime2](7) NULL,
	[pickup_origin_zip] [nvarchar](50) NULL,
	[pickup_origin_state] [nvarchar](50) NULL,
	[delivery_destination_zip] [nvarchar](50) NULL,
	[delivery_destination_state] [nvarchar](50) NULL,
	[shipment_weight_tons] [decimal](10, 2) NULL,
	[shipment_loaded_miles] [decimal](10, 2) NULL,
	[shipment_unloaded_miles] [decimal](10, 2) NULL,
	[shipment_mpg] [float] NULL,
	[shipment_fuel_type] [nvarchar](50) NULL,
	[asset_make_model] [nvarchar](100) NULL,
	[asset_vin] [nvarchar](100) NULL,
	[ev_asset] [nvarchar](10) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]