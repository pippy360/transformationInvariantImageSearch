def test_checksum():
    from transformation_invariant_image_search import models, main
    app = main.create_app(db_uri='sqlite://')
    csm_value = '54abb6e1eb59cccf61ae356aff7e491894c5ca606dfda4240d86743424c65faf'
    with app.app_context():
        models.DB.create_all()
        m = models.Checksum(value=csm_value, ext='png')
        models.DB.session.add(m)
        models.DB.session.commit()
        assert m.id == 1

        res = models.DB.session.query(models.Checksum).filter_by(id=1).first()
        assert res.value == csm_value
