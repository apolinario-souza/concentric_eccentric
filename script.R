# Pacotes
library(readxl)
library(dplyr)
library(afex)

setwd("C:/Users/lemeu/Desktop/bryan")

# Ler dados
dados <- read_excel("dados.xlsx")

# Selecionar apenas familiarização
fam <- dados %>%
  filter(fase == "familiarizacao")

# Transformar variáveis em fatores
fam$sujeito <- factor(fam$sujeito)
fam$acao <- factor(fam$acao,
                   levels = c("con", "exc"))

fam$bloco <- factor(fam$bloco)

# Variáveis dependentes
vars <- c(
  "TR_mean","TR_sd","TR_cv",
  "TM_mean","TM_sd","TM_cv",
  "EA_mean","EA_sd","EA_cv",
  "EC_mean","EC_sd","EC_cv",
  "PV_mean","PV_sd","PV_cv",
  "ETA_mean","ETA_sd","ETA_cv",
  "ETC_mean","ETC_sd","ETC_cv"
)

# Lista para armazenar resultados
resultados_anova <- list()

for(v in vars){
  
  formula_anova <- as.formula(
    paste(v, "~ acao * bloco + Error(sujeito/(acao*bloco))")
  )
  
  modelo <- aov_car(
    formula_anova,
    data = fam,
    factorize = FALSE
  )
  
  resultados_anova[[v]] <- modelo
  
  cat("\n=================================================\n")
  cat("Variável:", v, "\n")
  cat("=================================================\n")
  
  print(nice(modelo))
}

sink("Resultados_ANOVA_Familiarizacao.txt")

for(v in vars){
  
  cat("\n=================================================\n")
  cat("Variável:", v, "\n")
  cat("=================================================\n")
  
  print(nice(resultados_anova[[v]]))
}

sink()


library(readxl)
library(dplyr)
library(tidyr)

dados <- read_excel("dados.xlsx")

ret <- dados %>%
  filter(fase == "retencao")

vars <- c(
  "TR_mean","TR_sd","TR_cv",
  "TM_mean","TM_sd","TM_cv",
  "EA_mean","EA_sd","EA_cv",
  "EC_mean","EC_sd","EC_cv",
  "PV_mean","PV_sd","PV_cv",
  "ETA_mean","ETA_sd","ETA_cv",
  "ETC_mean","ETC_sd","ETC_cv"
)

resultados_t <- data.frame()

for(v in vars){
  
  temp <- ret %>%
    select(sujeito, acao, all_of(v)) %>%
    pivot_wider(
      names_from = acao,
      values_from = all_of(v)
    )
  
  teste <- t.test(
    temp$con,
    temp$exc,
    paired = TRUE
  )
  
  resultados_t <- rbind(
    resultados_t,
    data.frame(
      Variavel = v,
      t = teste$statistic,
      gl = teste$parameter,
      p = teste$p.value,
      Media_con = mean(temp$con, na.rm = TRUE),
      Media_exc = mean(temp$exc, na.rm = TRUE)
    )
  )
}

resultados_t

write.csv(
  resultados_t,
  "Resultados_Teste_t_Retencao.csv",
  row.names = FALSE
)
