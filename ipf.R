# Adapted from Lovelace 
# spatial-microsim-book.robinlovelace.net

######## Preparation ################
# install.packages("readxl") ##Install packages if necessary
# install.packages("mipfp")

# Need this for windows
if(.Platform$OS.type == "windows") Sys.setenv(PATH= paste("C:/Users/Sean/anaconda3/Library/bin",Sys.getenv()["PATH"],sep=";"))

## specify and load required packages, specify working directory
pkgs <- c("readxl","mipfp", "reticulate") 
lapply(pkgs, library, character.only = T)
use_condaenv("abm")
py_config()
# setwd("C:/XXX/XXX")
#####################################

####Read and format constraints
# age<-read_excel("Case Study 3 Data.xlsx", sheet=3)
age_and_sex = read.csv("rescaled_age.csv")
marital_status = read.csv("rescaled_marital_status.csv")
house_size = read.csv("rescaled_house_size.csv")
employment = read.csv("rescaled_employment.csv")
education = read.csv("rescaled_education.csv")

age_and_sex_names <- names(age_and_sex[1,-(1:2)])
marital_status_names <- names(marital_status[1,-(1:2)])
house_size_names <- names(house_size[1,-(1:2)])
employment_names <- names(employment[1,-(1:2)])
education_names <- names(education[1,-(1:2)])
names <- list(age_and_sex_names, marital_status_names, house_size_names, employment_names, education_names)

np <- import("numpy")
seed <- np$load("lfs_crosstab.npy")
seed <-array((as.matrix(seed)),dim=dim(seed), dimnames=names)

int_trs <- function(x){
  # For generalisation purpose, x becomes a vector
  xv <- as.vector(x) # allows trs to work on matrices
  xint <- floor(xv) # integer part of the weight
  r <- xv - xint # decimal part of the weight
  def <- round(sum(r)) # the deficit population
  # the weights be 'topped up' (+ 1 applied)
  topup <- sample(length(x), size = def, prob = r)
  xint[topup] <- xint[topup] + 1
  dim(xint) <- dim(x)
  dimnames(xint) <- dimnames(x)
  xint
}

int_expand_array <- function(x){
  # Transform the array into a dataframe
  count_data <- as.data.frame.table(x)
  # Store the indices of categories for the final population
  indices <- rep(1:nrow(count_data), count_data$Freq)
  # Create the final individuals
  ind_data <- count_data[indices,]
  ind_data
}

all_ed_ids = unlist(age_and_sex["ED_ID"])
for (i in (1:length(all_ed_ids))){
  ed <- all_ed_ids[i]
  
  age_and_sex.cons<-age_and_sex[i,-(1:2)]
  age_and_sex.cons<-unlist(age_and_sex.cons)
  
  marital_status.cons<-marital_status[i,-(1:2)]
  marital_status.cons<-unlist(marital_status.cons)
  
  house_size.cons<-house_size[i,-(1:2)]
  house_size.cons<-unlist(house_size.cons)
  
  employment.cons<-employment[i,-(1:2)]
  employment.cons<-unlist(employment.cons)
  
  education.cons<-education[i,-(1:2)]
  education.cons<-unlist(education.cons)
  
  ####Set seed and IPF parameters
  target <- list (age_and_sex.cons, marital_status.cons, house_size.cons, employment.cons, education.cons)
  descript <- list (1, 2, 3, 4, 5)

  ####Do IPF
  result <- Ipfp(seed, descript, target, tol = 1e-5)

  integerised <- int_trs(result$x.hat)
  only_non_zeros <- int_expand_array(integerised)
  
  if (grepl("/", ed, fixed = TRUE)) {
    ed <- gsub("/", "_", ed, fixed = TRUE)
  }
  
  write.csv(only_non_zeros, file=sprintf("results/ipf/%s.csv", ed))
}
