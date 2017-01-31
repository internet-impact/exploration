library(dplyr)



make.date.groups <- function (dates, thresh = .10) {
    l <- 25001
    base <- rep(NA, l)
    for (d in dates) {
        dat <- read.csv(paste0('../covered/', d, '-covered.csv'))
        base[dat$covered_percentage > thresh & is.na(base)] <- as.integer(d)
    }
    base
}

dates <- c("2009", "2011", "2012", "2013")
date.groups <- make.date.groups(dates)

dat.raw <- read.csv('../covered/2009-covered.csv')
dat.raw$year_treated <- date.groups

data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    group_by(year_treated) %>%
    summarise(mean_pop = mean(POP07), median_pop = median(POP07)) %>%
    ggplot(aes(x = year_treated, y = median_pop)) +
    geom_point()

data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    group_by(year_treated) %>%
    summarise(mean_pop = mean(POP07), median_pop = median(POP07)) %>%
    ggplot() +
    geom_point(aes(x = year_treated, y = mean_pop), colour = "orange") +
    geom_point(aes(x = year_treated, y = median_pop), colour = "blue")

data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    group_by(year_treated) %>%
    summarise(lower_10_pop= quantile(POP07, .1)) %>%
    ggplot(aes(x = year_treated, y = lower_10_pop)) +
    geom_point()

data.frame(dat.raw) %>%
    group_by(year_treated) %>%
    summarise(upper_10 = quantile(POP07, .9)) %>%
    ggplot(aes(x = year_treated, y = upper_10)) +
    geom_point()

data.frame(dat.raw) %>%
    group_by(year_treated) %>%
    summarise(upper_10 = quantile(GVA09, .9)) %>%
    ggplot(aes(x = year_treated, y = upper_10)) +
    geom_point()

data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    group_by(year_treated) %>%
    summarise(lower_10_gva= quantile(GVA09, .1)) %>%
    ggplot(aes(x = year_treated, y = lower_10_gva)) +
    geom_point()



data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    mutate(density = POP07/AREA_TOT) %>%
    ggplot(aes(x = year_treated, y = density*1000000)) +
    geom_point(alpha=.3) +
    labs(x="Year Internet Coverage First Exceeds 20%", y="Population Density (Per Sq. Km)")


data.frame(dat.raw) %>%
    filter(year_treated > 2009) %>%
    ggplot(aes(x = year_treated, y = GVA09)) +
    geom_point(alpha= .3)


summary(lm(year_treated ~ POP07 + GVA09, data = dat.raw))
