echo "Generating mocks from swagger yaml files"

YA_CLIENT_DIR=${1:-"../../../../ya-client/"}
YA_INT_ROOT="../../../"

echo "ya-client project location is '${YA_CLIENT_DIR}'"

if [ ! -d "$YA_CLIENT_DIR" ]; then
  echo "Error, ya-client directory not found" >&2
  exit 1
fi

openapi-generator version

if [ $? -ne 0 ]; then
  echo "Error, openapi-generator binary not found. Is it installed and added to your path?" >&2
  exit 1
fi

MOCK_OUTPUT_DIR="${YA_INT_ROOT}model/"
mkdir -p ${MOCK_OUTPUT_DIR}

function generate_client {
  echo "Generating client for ${1}"
  TARGET_DIR="${MOCK_OUTPUT_DIR}${1}"
  echo "Cleaning target directory: ${TARGET_DIR}"
  rm -rf ${TARGET_DIR}
  openapi-generator generate \
    --package-name "openapi_${1}_client" \
    -i "${YA_CLIENT_DIR}specs/${1}-api.yaml" \
    -g python \
    -o ${TARGET_DIR}
}

generate_client "market"
generate_client "activity"
generate_client "payment"
