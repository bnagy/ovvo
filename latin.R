library(ggplot2)
library(gridExtra)

# cool looking black theme for doing slide versions of the plots
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

analysis <- read.csv(file="U:\\Desktop\\pass4_cleaned.csv", header=TRUE, sep=",")

# Base scatterplot to draw lines on top of later
sp.empty <-ggplot(analysis) + geom_point(aes(x=date,y=pct_ov,color=lines,size=ov+vo,alpha=0.5)) + 
  scale_colour_gradient(low = "grey80", high = "grey0") +
  theme_bw() +
  scale_x_continuous(breaks = scales::pretty_breaks(n=10)) +
  scale_y_continuous(breaks = scales::pretty_breaks(n=10))

# do the plot  
sp.empty


# try a piecewise regression on every year from 300-500
# and record the mean squared error for each
# Create one that's weighted by work size and one non-weighted.
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
plot(index, mse.wts)
plot(index, mse.nowts)

#run the piecewise regression at the best cut
piecewise.wts <- lm(pct_ov ~ date*(date < cut.wts), data = analysis, weights = log(vo+ov))
piecewise.nowts <- lm(pct_ov ~ date*(date < cut.nowts), data = analysis)

# separate models, so we can get individial stats for each 'half'
# We're sampling more than once, so these p-values need to be multiplied
# by something. 10 is safe, and doesn't affect the conclusions.
subset.1.wts <- lm(pct_ov ~ date, data = subset(analysis, date < cut.wts), weights = log(vo+ov))
subset.2.wts <- lm(pct_ov ~ date, data = subset(analysis, date >= cut.wts), weights = log(vo+ov))
all.wts <- lm(pct_ov ~ date, data = analysis, weights = log(vo+ov))

# preditions based on piecewise models. We'll use these to plot
# the lines on top of sp.empty
pred.val.df = data.frame(date = seq(floor(min(analysis$date)), max(analysis$date), 1))
pred.val.df$predict.val.wts = predict(piecewise.wts, pred.val.df)
pred.val.df$predict.val.nowts = predict(piecewise.nowts, pred.val.df)

# not piecewise - use ggplot built in linear regression function
sp2 <- sp.empty + geom_smooth(data = analysis,aes(x = date, y = pct_ov, weight=log(ov+vo)),color="grey0",method='lm')
sp2

# piecewise, draw our predictions on top of the data
sp3 <- sp.empty + geom_line(data = pred.val.df, aes(x = date, y = predict.val.nowts, group = date >= cut.nowts), size = 1, colour = "grey20", linetype="longdash") +
  geom_line(data = pred.val.df, aes(x = date, y = predict.val.wts, group = date >= cut.wts), size = 1.4, colour = "grey0")
sp3

# produce summaries
summary(subset.1.wts)
summary(subset.2.wts)
summary(all.wts)


