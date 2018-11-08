library("ggplot2")
library(gridExtra)

# nice black theme for making presentation images
theme_black = function(base_size = 12, base_family = "") {
  
  theme_grey(base_size = base_size, base_family = base_family) %+replace%
    
    theme(
      # Specify axis options
      axis.line = element_blank(),  
      axis.text.x = element_text(size = base_size*0.8, color = "white", lineheight = 0.9),  
      axis.text.y = element_text(size = base_size*0.8, color = "white", lineheight = 0.9),  
      axis.ticks = element_line(color = "white", size  =  0.2),  
      axis.title.x = element_text(size = base_size, color = "white", margin = margin(0, 10, 0, 0)),  
      axis.title.y = element_text(size = base_size, color = "white", angle = 90, margin = margin(0, 10, 0, 0)),  
      axis.ticks.length = unit(0.3, "lines"),   
      # Specify legend options
      legend.background = element_rect(color = NA, fill = "black"),  
      legend.key = element_rect(color = "white",  fill = "black"),  
      legend.key.size = unit(1.2, "lines"),  
      legend.key.height = NULL,  
      legend.key.width = NULL,      
      legend.text = element_text(size = base_size*0.8, color = "white"),  
      legend.title = element_text(size = base_size*0.8, face = "bold", hjust = 0, color = "white"),  
      legend.position = "right",  
      legend.text.align = NULL,  
      legend.title.align = NULL,  
      legend.direction = "vertical",  
      legend.box = NULL, 
      # Specify panel options
      panel.background = element_rect(fill = "black", color  =  NA),  
      panel.border = element_rect(fill = NA, color = "white"),  
      panel.grid.major = element_line(color = "grey35"),  
      panel.grid.minor = element_line(color = "grey20"),  
      panel.spacing = unit(0.5, "lines"),   
      # Specify facetting options
      strip.background = element_rect(fill = "grey30", color = "grey10"),  
      strip.text.x = element_text(size = base_size*0.8, color = "white"),  
      strip.text.y = element_text(size = base_size*0.8, color = "white",angle = -90),  
      # Specify plot options
      plot.background = element_rect(color = "black", fill = "black"),  
      plot.title = element_text(size = base_size*1.2, color = "white"),  
      plot.margin = unit(rep(1, 4), "lines")
      
    )
  
}
analysis <- read.csv(file="U:\\Desktop\\analysis_nopoets.csv", header=TRUE, sep=",")

# Base scatterplot to draw lines on top of later
sp.empty <-ggplot(analysis) + geom_point(aes(x=date,y=pct_ov,color=lines,size=ov+vo,alpha=0.5)) + 
  scale_colour_gradient(low = "grey80", high = "grey0") +
  theme_bw() +
  scale_x_continuous(breaks = scales::pretty_breaks(n=10)) +
  scale_y_continuous(breaks = scales::pretty_breaks(n=10)) +
  theme(legend.position="none") +
  labs(x="Year (Negative dates are BCE)", y="% OV word order")
  
sp.empty
# ggsave("U:\\Desktop\\sp_empty.pdf", plot=sp.empty, width=7, height=5.25)

# try a piecewise regression on every year from 300-500
# and record the mean squared error for each
index  <- c(301:500)
mse.wts <- numeric(length(index))
mse.nowts <- numeric(length(index))
for(idx in 1:length(index)){
  i = index[idx]
  piecewise.wts <- lm(pct_ov ~ date*(date < i), data = analysis, weights = log(vo+ov))
  piecewise.nowts <- lm(pct_ov ~ date*(date < i), data = analysis)
  mse.wts[idx] <- summary(piecewise.wts)$sigma
  mse.nowts[idx] <- summary(piecewise.nowts)$sigma
}

mse.wts = unlist(mse.wts)
mse.nowts = unlist(mse.nowts)
# cut the regression at the year with the best MSE
cut.wts = index[which.min(mse.wts)]
cut.nowts = index[which.min(mse.nowts)]

#error graphs
#plot(index, mse.wts)
#plot(index, mse.nowts)
# Create a new dataframe
mse.wts.df = data.frame(index = index, errs = mse.wts)
# and ggplot the stuff
sp.mse <-ggplot(mse.wts.df) + geom_point(aes(x=index,y=errs,alpha=0.3),size=3) + 
  theme_bw() +
  scale_x_continuous(breaks = scales::pretty_breaks(n=10)) +
  scale_y_continuous(breaks = scales::pretty_breaks(n=10)) +
  theme(legend.position="none") +
  labs(x="Year", y="Mean Squared Error")
# ggsave("U:\\Desktop\\sp_mse.pdf", plot=sp.mse, width=7, height=5.25)

sp.mse
#run best models
piecewise.wts <- lm(pct_ov ~ date*(date < cut.wts), data = analysis, weights = log(vo+ov))
piecewise.nowts <- lm(pct_ov ~ date*(date < cut.nowts), data = analysis)

# separate models
subset.1.wts <- lm(pct_ov ~ date, data = subset(analysis, date < cut.wts), weights = log(vo+ov))
subset.2.wts <- lm(pct_ov ~ date, data = subset(analysis, date >= cut.wts), weights = log(vo+ov))
all.wts <- lm(pct_ov ~ date, data = analysis, weights = log(vo+ov))

# preditions based on piecewise models
pred.val.df = data.frame(date = seq(floor(min(analysis$date)), max(analysis$date), 1))
pred.val.df$predict.val.wts = predict(piecewise.wts, pred.val.df)
pred.val.df$predict.val.nowts = predict(piecewise.nowts, pred.val.df)

# not piecewise
sp2 <- sp.empty + 
  geom_smooth(data = analysis,aes(x = date, y = pct_ov, weight=log(ov+vo)),color="grey0",method='lm') +
  theme(legend.position="none") +
  labs(x="Year (Negative dates are BCE)", y="% OV word order")
sp2
# ggsave("U:\\Desktop\\sp_single_lm.pdf", plot=sp2, width=7, height=5.25)


# piecewise
sp3 <- sp.empty + 
  # geom_line(data = pred.val.df, aes(x = date, y = predict.val.nowts, group = date >= cut.nowts), size = 1, colour = "grey10", linetype="longdash") +
  geom_line(data = pred.val.df, aes(x = date, y = predict.val.wts, group = date >= cut.wts), size = 1, colour = "grey10") +
  theme(legend.position="none") +
  labs(x="Year (Negative dates are BCE)", y="% OV word order")
sp3
# ggsave("U:\\Desktop\\sp_piecewise_lm.pdf", plot=sp3, width=7, height=5.25)

summary(subset.1.wts)
summary(subset.2.wts)
summary(all.wts)



# Method 1
# author_summary = data.frame(author = unique(analysis$author), sd = NA, min = NA, max = NA, works = NA)
# for (i in 1:nrow(author_summary)){
#   aut = author_summary[i, 'author']
#   author_summary[i, 'sd'] = sd(subset(analysis, author == aut)$pct_ov)
#   author_summary[i, 'min'] = min(subset(analysis, author == aut)$pct_ov)
#   author_summary[i, 'max'] = max(subset(analysis, author == aut)$pct_ov)
#   author_summary[i, 'works'] = nrow(subset(analysis, author == aut))
# }


# Method 2
library(plyr)
author_summary = ddply(analysis, 'author', summarise, sd = sd(pct_ov), min = min(pct_ov), max = max(pct_ov), works = length(pct_ov), mean_date = mean(date))

# Sorting 
author_summary = author_summary[order(author_summary$sd), ]
author_summary = author_summary[order(author_summary$sd, decreasing = TRUE), ]

# plot variation by unique author by date
sp.authorvar <-ggplot(author_summary) + geom_point(aes(x=mean_date,y=sd,alpha=0.6),size=2.5) + 
  theme_bw() +
  scale_x_continuous(breaks = scales::pretty_breaks(n=10)) +
  scale_y_continuous(breaks = scales::pretty_breaks(n=10)) +
  geom_smooth(data = author_summary,aes(x = mean_date, y = sd),color="grey0",method="loess") +
  theme(legend.position="none") +
  labs(x="Year (Negative dates are BCE)", y="Standard Deviation in % OV (per author)")
sp.authorvar
# ggsave("U:\\Desktop\\sp_authorvar.pdf", plot=sp.authorvar, width=7, height=5.25)

# extract raw data to look at
author_summary = author_summary[order(author_summary$sd), ]
head(subset(author_summary, works >= 5))
head(subset(author_summary[order(author_summary$sd, decreasing = TRUE), ], works >= 5))
author_summary_5works <- subset(author_summary, works >= 5)
# write.csv(author_summary_5works,file="author_summary_5works.csv")




