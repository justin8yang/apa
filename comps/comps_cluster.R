library(amap)

args = commandArgs(trailingOnly = T); # trailingOnly: only take parameters after --args
input_filename = args[1];
output_filename = args[2];
num_control = as.numeric(args[3]);
num_test = as.numeric(args[4]);
comps_id = args[5];
offset = 10

data <- read.delim(input_filename,row.names=NULL)
z = data[, offset:(offset+num_control+num_test-1)]
colnames(z)
# transpose matrix, since we dont want distances between rows (genes), but between experiments (columns)
z = t(as.matrix(z))
d <- Dist(z, method="spearman")
hc <- hclust(d, method="ward.D")

require(graphics)
svg(output_filename, width=10, height=7, pointsize=10, bg="transparent")
op <- par(mar = par("mar") + c(1,1,1,12))
#op <- par(mai = c(1,1,1,6), xpd = NA)
plot(as.dendrogram(hc), main=comps_id, horiz=T)
dev.off()
