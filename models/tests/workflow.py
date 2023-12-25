import unittest
import sys
# fmt: off
sys.path.append('/Users/jiayangsun/Documents/github/cap/proxy')

from models.workflow import WorkflowMetadata, WorkflowType
from unittest.mock import ANY

TEST_USER_ID = 0


class WorkflowMetadataTest(unittest.TestCase):

    def test_list_return_no_empty(self) -> None:
        metadatas = WorkflowMetadata.list(TEST_USER_ID, WorkflowType.VIDEO)
        self.assertEquals(len(metadatas), 1)

        # WorkflowMetadata(id=45, create_at=1701579219, status=7, uuid='3g5KGYyneGw', snippt={}, transcript=ANY)
        metadata = metadatas[0]
        self.assertEqual(metadata.id, 45)
        self.assertEqual(metadata.uuid, "3g5KGYyneGw")
        self.assertEqual(metadata.snippt, {})


# python3 models/tests/workflow.py
if __name__ == '__main__':
    unittest.main()
