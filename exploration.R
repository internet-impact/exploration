if (!require("pacman")) install.packages("pacman")
pacman::p_load(
  sp,
  rgdal,
  rgeos,
  raster,
  maptools,
  leaflet,
  foreach,
  doParallel
)


#########################
# Parallel
cl <- makeCluster(detectCores())
registerDoParallel(cl)


############################
# Load Data
mobile.data <- readOGR(dsn = "data/2009/Data/3G")
mobile.data <- spTransform(mobile.data, CRS(proj4string(mobile.data)))
mobile.data <- gBuffer(mobile.data, width = 0)
gIsValid(mobile.data)

econ.data <- readOGR(dsn = "MESO/meso_2010_econ_dd")
econ.data <- spTransform(econ.data, CRS(proj4string(mobile.data)))
gIsValid(econ.data)


lil.econ <- econ.data[econ.data@data$POP07 > 30000, ]

bind.null <- function (a,b) {
  if (is.null(b)) return (a)
  rbind(a,b)
}

# MUTATES base!!
calc.coverage <- function (base, inter, id = 'MESO_ID') {
  areas <- data.frame(covered_area= sapply(inter@polygons, function (p) p@area))
  inter$covered_area <- areas

  # Let's hope the order stayed the same...
  base[!base@data[, id] %in% inter@data[, id], 'covered_area'] <- 0
  base[base@data[,id] %in% inter@data[, id], 'covered_area'] <- inter$covered_area
  base$covered_percentage <- base$covered_area/base$AREA
  base
}

make.intersection <- function (base, mobile, chunks = detectCores()) {
  N <- nrow(base)
  n <- ceiling(N/chunks)

  foreach(i = seq(1,N,n), .combine = bind.null) %dopar% {
    chunk <- base[i:min(i + n-1, N), ]
    raster::intersect(chunk, mobile)
  }
}

# plot
plot.coverage <- function (dat) {
  qpal <- colorBin("Blues", dat$covered_percentage, n = 7)
  leaflet(dat) %>%
    addTiles() %>%
    addPolygons(color = ~qpal(covered_percentage)) %>%
    addLegend(pal = qpal, values = ~covered_percentage, opacity = .5)
}


find.layer <- function (file) {
    layers <- ogrListLayers(file)
    layers[grepl("Global", layers)]
}

make.econ.sets <- function (dates) {
    for (d in dates) {
        file <- paste0('data/', d, '/Data/3G')
        layer <- find.layer(file)
        mobile.data <- readOGR(dsn = file, layer = layer)
        mobile.data <- spTransform(mobile.data, CRS(proj4string(mobile.data)))
        mobile.data <- gBuffer(mobile.data, width = 0)
        covered <- calc.coverage(make.intersection(base, mobile))
        write.csv(covered, paste0(d, '-covered.csv'))
    }
}

get.intersected.area <- function (base, mobile, id = 'MESO_ID') {
    inter <- raster::intersect(base, mobile)

    areas <- data.frame(covered_area= sapply(inter@polygons, function (p) p@area))
    inter$covered_area <- areas

                                        # Let's hope the order stayed the same...
    base[!base@data[, id] %in% inter@data[, id], 'covered_area'] <- 0
    base[base@data[,id] %in% inter@data[, id], 'covered_area'] <- inter$covered_area
    base$covered_percentage <- base$covered_area/base$AREA
    base
}


dates <- c('2009', '2011', '2012', '2013', '2014', '2015')


check.conversion <- function (old.df, new.df){
    d <- data.frame(layer = new.df$layer, area = area(new.df))
    d <- d[order(d$layer), ]
    sum((d$area - area(old.df))^2)
}
