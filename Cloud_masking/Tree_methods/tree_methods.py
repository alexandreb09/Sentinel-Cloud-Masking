#####################################################
# Fonctions performing tree mask methods            #
# Methods:                                          #
#   - normalizedImage(image, coef_standard=10000)   #
#   - getMaskTree1(image, roi)                      #
#   - getMaskTree2(image, roi)                      #
#   - getMaskTree3(image, roi)                      #
#####################################################

from parameters import COEF_NORMALISATION

def normalizedImage(image, coef_standard=COEF_NORMALISATION):
    """ Normalize image band values (same scale as in the article)
    Arguments:
        :param image: 
        :param coef_standard=COEF_NORMALISATION: reduction coefficient 
                             (see "parameter.py" file for the value)
    """ 
    # Normalization image according to article
    return image.divide(coef_standard)


####################################
# Compute Decision Tree filter 1   #
####################################
def getMaskTree1(image, roi):
    """ Compute tree1 method
    Argument
        :param image: image to process
        :param roi: region_of_interest
    """
    image_normalized = normalizedImage(image)

    # Criteria 1 : Cirrus
    expr1 = image_normalized.expression(
        '( (b("B3") < 0.325) && (b("B8A") < 0.166) && (b("B10") > 0.011)) ? 1 : 0'
    )
    # Criteria 2 : Cirrus
    expr2 = image_normalized.expression(
        '( (b("B3") > 0.325) && (b("B11") < 0.267) && (b("B4") < 0.674)) ? 1 : 0'
    )
    # Criteri 3 : Clouds
    expr3 = image_normalized.expression(
        '( (b("B3") > 0.325) && (b("B11") > 0.267) && (b("B7") < 1.544)) ? 1 : 0'
    )
    # full criteria = Clouds + Cirrus
    return expr1.Or(expr2.Or(expr3)).select(["constant"], ["tree1"]).clip(roi)


####################################
# Compute Decision Tree filter 2   #
####################################
def getMaskTree2(image, roi):
    """ Compute tree2 method
    Argument
        :param image: image to process
        :param roi: region_of_interest
    """
    image_normalized = normalizedImage(image)

    # Criteria 1 : Cirrus
    expr1 = image_normalized.expression(
        '( (b("B8A") > 0.156) && (b("B3") < 0.333) && (b("B10")/b("B2") > 0.065)) ? 1 : 0'
    )
    # Criteria 2 : Cloud
    expr2 = image_normalized.expression(
        '( (b("B8A") > 0.156) && (b("B3") > 0.333) && (b("B6")/b("B11") < 4.292)) ? 1 : 0'
    )
    # full criteria = Clouds + Cirrus
    return expr1.Or(expr2).select(["constant"], ["tree2"]).clip(roi)


####################################
# Compute Decision Tree filter 3   #
####################################
def getMaskTree3(image, roi):
    """ Compute tree3 method
    Argument
        :param image: image to process
        :param roi: region_of_interest
    """
    image_normalized = normalizedImage(image)

    # Criteria 1 : Cirrus
    expr1 = image_normalized.expression(
        '( (b("B8A") < 0.181) && (b("B8A") > 0.051) && (b("B12") < 0.097) && (b("B10") > 0.011)) ? 1 : 0'
    )
    # Criteria 2 : Cloud
    expr2 = image_normalized.expression(
        '( (b("B8A") > 0.181) && (b("B1") < 0.331) && (b("B10") < 0.012) && (b("B2") > 0.271) ) ? 1 : 0'
    )

    # Criteria 3 : Cirrus
    expr3 = image_normalized.expression(
        '( (b("B8A") > 0.181) && (b("B1") < 0.331) && (b("B10") > 0.012) ) ? 1 : 0'
    )

    # Criteria 4 : Cirrus
    expr4 = image_normalized.expression(
        '( (b("B8A") > 0.181) && (b("B1") > 0.331) && (b("B11") < 0.239) && (b("B2") < 0.711) ) ? 1 : 0'
    )

    # Criteria 5 : Cloud
    expr5 = image_normalized.expression(
        '( (b("B8A") > 0.181) && (b("B1") > 0.331) && (b("B11") > 0.239) && (b("B5") < 1.393) ) ? 1 : 0'
    )

    # full criteria = Clouds + Cirrus
    return expr1.Or(expr2.Or(expr3.Or(expr4.Or(expr5)))).select(["constant"], ["tree3"]).clip(roi)
