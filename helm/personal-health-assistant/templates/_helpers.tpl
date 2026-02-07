{{/*
Expand the name of the chart.
*/}}
{{- define "personal-health-assistant.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "personal-health-assistant.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "personal-health-assistant.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "personal-health-assistant.labels" -}}
helm.sh/chart: {{ include "personal-health-assistant.chart" . }}
{{ include "personal-health-assistant.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "personal-health-assistant.selectorLabels" -}}
app.kubernetes.io/name: {{ include "personal-health-assistant.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "personal-health-assistant.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "personal-health-assistant.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create image name
*/}}
{{- define "personal-health-assistant.image" -}}
{{- $registry := .Values.global.imageRegistry | default "ghcr.io" }}
{{- $repository := .Values.image.repository }}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}

{{/*
Service image helper
*/}}
{{- define "personal-health-assistant.serviceImage" -}}
{{- $registry := .global.imageRegistry | default "ghcr.io" }}
{{- $baseRepo := .global.imageRepository | default "ppulimamidy/personalhealthassistant" }}
{{- $serviceName := .service.image.repository }}
{{- $tag := .service.image.tag | default "latest" }}
{{- printf "%s/%s/%s:%s" $registry $baseRepo $serviceName $tag }}
{{- end }}
