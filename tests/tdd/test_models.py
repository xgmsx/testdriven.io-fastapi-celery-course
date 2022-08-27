# from project.tdd.factories import MemberFactory
#
#
# def old_test_model(db_session, member):
#     member = MemberFactory.build()
#     db_session.add(member)
#     db_session.commit()
#
#     assert member.id

def test_model(db_session, member):
    assert member.username
    assert member.avatar
    assert not member.avatar_thumbnail
