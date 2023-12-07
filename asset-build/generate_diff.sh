## generate code changes the way github auto-generates.
## this will produce the list of PRs merged between a previous release and current code.

CUR_REL=${RELEASE}
# CUR_REL_NAME = the name of the current release, without the build number. i.e. 3.1-100 --> 3.1
CUR_REL_NAME=$(echo ${CUR_REL} | awk -F"-" '{$NF="";print}')
# find the latest build that is not matching current release name
OLD_REL=$(git tag -l "[1-9].*" | sort -Vr | grep -v ${CUR_REL_NAME} | head -n1)
cd /psdiag
git log --graph --pretty=format:'%Cred%h%Creset %C(bold blue)<%s>%Creset - %b %>|(-33)%Cgreen(%cD)' --abbrev-commit --first-parent ${OLD_REL}..HEAD
if [[ $? -ne 0 ]]; then echo "Unable to generate diff between ${OLD_REL}..${CUR_REL}"; fi
