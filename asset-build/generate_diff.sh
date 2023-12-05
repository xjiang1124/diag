## generate code changes the way github auto-generates.
## this will produce the list of PRs merged between a previous release and current code.

search_previous_rel() {
    # CUR_REL_NAME = the name of the current release, without the build number. i.e. 3.1-100 --> 3.1
    CUR_REL_NAME=$(echo ${RELEASE} | awk -F"-" '{$NF="";print $0}')
    # pull the latest build that is not matching current release name
    asset-pull --bucket builds --list hourly-diag | sort -Vr | grep -v ${CUR_REL_NAME} | head -n1
}
WORKDIR=/psdiag
CUR_REL=${RELEASE}
OLD_REL=$(search_previous_rel)
git log --graph --pretty=format:'%Cred%h%Creset %C(bold blue)<%s>%Creset - %b %>|(-33)%Cgreen(%cD)' --abbrev-commit --first-parent ${OLD_REL}..${CUR_REL}
